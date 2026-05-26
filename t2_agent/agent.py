"""DeepSeek function-calling agent loop for T2 workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .deepseek import DEEPSEEK_BASE_URL
from .guidance import build_parameter_guidance, infer_requested_plan
from .models import AgentToolResult
from .skills import render_skill_prompt
from .tools import (
    generate_report,
    inspect_workbook_schema,
    interpret_results,
    plot_decay_spectrum,
    repair_workbook,
    run_fixed_nnls,
    run_gaussian_peaks,
    run_lcurve,
    validate_workbook,
)


@dataclass
class AgentRuntimeContext:
    """Mutable per-session state used by whitelisted tools."""

    workspace: Path
    uploaded_path: Path | None = None
    validation: AgentToolResult | None = None
    repaired_path: Path | None = None
    spectrum_path: Path | None = None
    results: list[AgentToolResult] = field(default_factory=list)
    tool_history: list[AgentToolResult] = field(default_factory=list)
    report: AgentToolResult | None = None
    last_user_goal: str = ""


@dataclass
class AgentTurnResult:
    """Result of one chat turn, including tools the model chose to run."""

    assistant_message: str
    messages: list[dict[str, Any]]
    tool_results: list[AgentToolResult]
    trace: list[dict[str, Any]] = field(default_factory=list)


def build_tool_specs() -> list[dict[str, Any]]:
    """Return OpenAI-compatible tool schemas for DeepSeek."""

    return [
        {
            "type": "function",
            "function": {
                "name": "inspect_workbook_schema",
                "description": "读取当前上传 Excel 的结构、前几行预览、列名、数值范围和单调性，帮助 AI 判断非标准格式。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "preview_rows": {"type": "integer", "description": "预览行数，默认 8。"}
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "validate_workbook",
                "description": "检查当前上传的 Excel 数据格式，判断是否能做 T2 反演或分峰。",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repair_workbook",
                "description": "把当前上传的 Excel 自动整理成标准 time_ms + signal columns 格式。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_to_ms_scale": {
                            "type": "number",
                            "description": "把原始时间转换成 ms 的倍数。秒用 1000，已是 ms 用 1。",
                        }
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_lcurve",
                "description": "对标准化 decay 数据运行 L-curve T2 反演，自动选择平滑因子。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "t2_min_ms": {"type": "number", "description": "T2 搜索下限，默认 0.01 ms。"},
                        "t2_max_ms": {"type": "number", "description": "T2 搜索上限，默认 100000 ms。"},
                        "num_bins": {"type": "integer", "description": "T2 bins 数量，默认 200。"},
                        "alpha_count": {"type": "integer", "description": "L-curve 测试的平滑因子数量，默认 60。"},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_fixed_nnls",
                "description": "用户明确指定平滑因子时，运行固定正则化 NNLS T2 反演。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "regularization": {"type": "number", "description": "固定平滑因子。"},
                        "t2_min_ms": {"type": "number", "description": "T2 搜索下限，默认 1 ms。"},
                        "t2_max_ms": {"type": "number", "description": "T2 搜索上限，默认 10000 ms。"},
                        "num_bins": {"type": "integer", "description": "T2 bins 数量，默认 200。"},
                    },
                    "required": ["regularization"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "plot_decay_spectrum",
                "description": "生成 decay 曲线和 T2 spectrum 的配对图。",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_gaussian_peaks",
                "description": "对当前 T2 spectrum 运行 Gaussian 分峰。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "peak_count": {"type": "integer", "description": "分峰数量，例如 2 或 3。", "minimum": 1, "maximum": 8}
                    },
                    "required": ["peak_count"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "generate_report",
                "description": "根据当前工具结果生成中文 Markdown 报告。",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "interpret_results",
                "description": "读取已经生成的 summary、T2 spectrum、Gaussian peak table，并解释结果说明了什么。",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
    ]


def _result_payload(result: AgentToolResult) -> str:
    return json.dumps(
        {
            "status": result.status,
            "message": result.message,
            "artifacts": result.artifacts,
            "summary": result.summary,
            "error": result.error,
        },
        ensure_ascii=False,
        default=str,
    )


def _require_upload(context: AgentRuntimeContext) -> AgentToolResult | None:
    if context.uploaded_path is None:
        return AgentToolResult("failed", "还没有上传 Excel 文件。请先上传数据，再让我检查或运行。", error="missing_upload")
    return None


def execute_agent_tool(name: str, args: dict[str, Any], context: AgentRuntimeContext) -> AgentToolResult:
    """Execute one whitelisted tool and update runtime context."""

    if name in {"inspect_workbook_schema", "validate_workbook", "repair_workbook"}:
        missing = _require_upload(context)
        if missing:
            return missing

    if name in {"run_lcurve", "run_fixed_nnls"} and context.repaired_path is None:
        return AgentToolResult("failed", "反演前需要先调用 repair_workbook 生成标准化 Excel。", error="missing_repaired_workbook")

    if name == "inspect_workbook_schema":
        return inspect_workbook_schema(context.uploaded_path, int(args.get("preview_rows", 8)))  # type: ignore[arg-type]

    if name == "validate_workbook":
        result = validate_workbook(context.uploaded_path)  # type: ignore[arg-type]
        context.validation = result
        return result

    if name == "repair_workbook":
        scale = args.get("time_to_ms_scale")
        if scale is None and context.validation is not None:
            scale = context.validation.summary.get("recommended_time_to_ms_scale", 1.0)
        result = repair_workbook(context.uploaded_path, context.workspace / "standardized", float(scale or 1.0))  # type: ignore[arg-type]
        if result.status == "success" and result.artifacts:
            context.repaired_path = Path(result.artifacts[0])
        return result

    if name == "run_lcurve":
        params = {
            "time_to_ms_scale": 1.0,
            "t2_min_ms": float(args.get("t2_min_ms", 1e-2)),
            "t2_max_ms": float(args.get("t2_max_ms", 1e5)),
            "num_bins": int(args.get("num_bins", 200)),
            "alpha_count": int(args.get("alpha_count", 60)),
        }
        result = run_lcurve(context.repaired_path, context.workspace / "lcurve", params)  # type: ignore[arg-type]
        context.results.append(result)
        if result.status == "success" and "spectrum_xlsx" in result.summary:
            context.spectrum_path = Path(result.summary["spectrum_xlsx"])
        return result

    if name == "run_fixed_nnls":
        params = {
            "time_to_ms_scale": 1.0,
            "regularization": float(args["regularization"]),
            "t2_min_ms": float(args.get("t2_min_ms", 1.0)),
            "t2_max_ms": float(args.get("t2_max_ms", 1e4)),
            "num_bins": int(args.get("num_bins", 200)),
        }
        result = run_fixed_nnls(context.repaired_path, context.workspace / "nnls", params)  # type: ignore[arg-type]
        context.results.append(result)
        if result.status == "success" and "spectrum_xlsx" in result.summary:
            context.spectrum_path = Path(result.summary["spectrum_xlsx"])
        return result

    if name == "plot_decay_spectrum":
        if context.repaired_path is None or context.spectrum_path is None:
            return AgentToolResult("failed", "画图前需要已有标准化 decay 文件和 T2 spectrum 文件。", error="missing_plot_inputs")
        result = plot_decay_spectrum(context.repaired_path, context.spectrum_path, context.workspace / "plots", {"time_to_ms_scale": 1.0})
        context.results.append(result)
        return result

    if name == "run_gaussian_peaks":
        if context.spectrum_path is None:
            return AgentToolResult("failed", "分峰前需要先完成 T2 反演或上传 T2 spectrum。", error="missing_spectrum")
        result = run_gaussian_peaks(context.spectrum_path, context.workspace / "gaussian", {"peak_count": int(args["peak_count"])})
        context.results.append(result)
        return result

    if name == "generate_report":
        goal = context.last_user_goal or "用户希望由 Agent 自动完成 T2 数据处理。"
        plan = infer_requested_plan(goal)
        result = generate_report(
            context.workspace / "report",
            user_goal=goal,
            validation=context.validation or AgentToolResult("failed", "尚未完成数据诊断。", error="missing_validation"),
            workflow_results=context.results,
            parameter_notes=build_parameter_guidance(plan),
        )
        context.report = result
        return result

    if name == "interpret_results":
        result = interpret_results(context.results, context.workspace / "interpretation")
        context.results.append(result)
        return result

    return AgentToolResult("failed", f"未知工具：{name}", error="unknown_tool")


def _assistant_to_dict(message: Any) -> dict[str, Any]:
    if hasattr(message, "model_dump"):
        data = message.model_dump()
    else:
        data = {
            "role": "assistant",
            "content": getattr(message, "content", None),
            "tool_calls": getattr(message, "tool_calls", None),
        }
    data["role"] = "assistant"
    return {key: value for key, value in data.items() if value is not None}


def run_deepseek_agent_turn(
    *,
    api_key: str,
    model: str,
    thinking_enabled: bool,
    user_message: str,
    context: AgentRuntimeContext,
    prior_messages: list[dict[str, Any]],
    client: Any | None = None,
    max_tool_rounds: int = 6,
    on_trace: Callable[[dict[str, Any]], None] | None = None,
    response_language: str = "中文",
) -> AgentTurnResult:
    """Run one DeepSeek chat turn with real function calling."""

    if client is None:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)

    context.last_user_goal = user_message
    messages = list(prior_messages)
    language_instruction = "Reply in English." if response_language.lower().startswith("english") else "请用中文回复。"
    if not any(message.get("role") == "system" for message in messages):
        messages.insert(
            0,
            {
                "role": "system",
                "content": (
                    "你是一个真正会调用工具的 NMR T2 反演 Agent。必须先调用 inspect_workbook_schema 查看表格结构，"
                    "再调用 validate_workbook 检查数据，但这条规则只适用于用户已经上传数据并要求检查/运行/解释数据时。"
                    "如果用户只是询问你能做什么、参数含义、能力边界、数据格式要求、工作流程或使用建议，不要调用工具，直接讲清楚。"
                    "不要假设第一列一定是时间；要根据列名、单调性、数值范围和预览判断。"
                    "如果 Time 列在第二列、Peak 列在第一列，这通常是列顺序不符合旧工具预期，不要误称为列名写反。"
                    "只有当列名和数值形态互相矛盾时，才说列名可能错误。"
                    "如果发现列顺序不符合工具预期、表头不在预期位置、多信号列或非标准布局，要明确告诉用户并调用 repair_workbook 标准化。"
                    "用户不懂参数时，优先 repair_workbook + run_lcurve；"
                    "用户明确指定平滑因子时，使用 run_fixed_nnls；用户要求分峰时，在已有 spectrum 后调用 run_gaussian_peaks。"
                    "当用户问“解释结果”“结果说明什么”“这个结果怎么样”“下一步怎么分析”时，必须调用 interpret_results，"
                    "不要只让用户看右侧工具结果。"
                    "你不能声称已经运行工具，除非本轮消息里确实收到对应 tool 结果。"
                    "回答面向新手，解释平滑因子、L-curve、T2 范围、分峰数量的作用。"
                    f"{language_instruction}"
                    f"\n\n{render_skill_prompt()}"
                ),
            },
        )

    messages.append({"role": "user", "content": user_message})
    tool_results: list[AgentToolResult] = []
    trace: list[dict[str, Any]] = [
        {
            "kind": "plan",
            "message": "本轮先让模型判断是否需要调用工具；若模型请求工具，只执行白名单 T2 tools。",
        }
    ]
    if on_trace:
        on_trace(trace[0])
    tools = build_tool_specs()

    for _ in range(max_tool_rounds):
        kwargs = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.2,
            "extra_body": {"thinking": {"type": "enabled" if thinking_enabled else "disabled"}},
        }
        response = client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        tool_calls = getattr(message, "tool_calls", None) or []
        messages.append(_assistant_to_dict(message))

        if not tool_calls:
            return AgentTurnResult(message.content or "", messages, tool_results, trace)

        for tool_call in tool_calls:
            name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            trace.append(
                {
                    "kind": "tool_call",
                    "tool_name": name,
                    "arguments": args,
                    "message": f"AI 请求调用工具 `{name}`。",
                }
            )
            if on_trace:
                on_trace(trace[-1])
            result = execute_agent_tool(name, args, context)
            tool_results.append(result)
            context.tool_history.append(result)
            trace.append(
                {
                    "kind": "tool_result",
                    "tool_name": name,
                    "status": result.status,
                    "message": result.message,
                    "error": result.error,
                    "summary_keys": sorted(result.summary.keys()),
                    "artifact_count": len(result.artifacts),
                }
            )
            if on_trace:
                on_trace(trace[-1])
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": _result_payload(result)})

    fallback = "我已经调用了多轮工具，但还没有得到最终回复。请查看右侧工具结果，或让我继续分析。"
    return AgentTurnResult(fallback, messages, tool_results, trace)
