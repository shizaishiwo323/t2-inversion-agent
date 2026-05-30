"""DeepSeek function-calling agent loop for T2 workflows."""

from __future__ import annotations

import json
import re
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
    uploaded_paths: list[Path] = field(default_factory=list)
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
                "description": "Read the uploaded Excel structure, preview rows, column labels, numeric ranges, and monotonicity so the agent can reason about nonstandard layouts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "preview_rows": {"type": "integer", "description": "Number of preview rows. Default: 8."}
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
                "description": "Validate the uploaded Excel format and decide whether it can be used for T2 inversion or peak decomposition.",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "repair_workbook",
                "description": "Normalize the uploaded Excel workbook into the standard time_ms + signal columns format.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "time_to_ms_scale": {
                            "type": "number",
                            "description": "Multiplier that converts raw time to ms. Use 1000 for seconds and 1 when the data is already in ms.",
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
                "description": "Run L-curve T2 inversion on standardized decay data and select the smoothing factor automatically.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "t2_min_ms": {"type": "number", "description": "Lower bound for the T2 search range. Default: 0.01 ms."},
                        "t2_max_ms": {"type": "number", "description": "Upper bound for the T2 search range. Default: 100000 ms."},
                        "num_bins": {"type": "integer", "description": "Number of T2 bins. Default: 200."},
                        "alpha_count": {"type": "integer", "description": "Number of smoothing factors tested by L-curve. Default: 60."},
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
                "description": "Run fixed-regularization NNLS T2 inversion when the user explicitly specifies a smoothing factor.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "regularization": {"type": "number", "description": "Fixed smoothing/regularization factor."},
                        "t2_min_ms": {"type": "number", "description": "Lower bound for the T2 search range. Default: 1 ms."},
                        "t2_max_ms": {"type": "number", "description": "Upper bound for the T2 search range. Default: 10000 ms."},
                        "num_bins": {"type": "integer", "description": "Number of T2 bins. Default: 200."},
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
                "description": "Generate paired decay-curve and T2-spectrum figures.",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_gaussian_peaks",
                "description": "Run Gaussian peak decomposition on the current T2 spectrum.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "peak_count": {"type": "integer", "description": "Number of peaks, for example 2 or 3.", "minimum": 1, "maximum": 8}
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
                "description": "Generate a Markdown report in the requested user-facing language from the current tool results.",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "interpret_results",
                "description": "Read generated summaries, T2 spectra, and Gaussian peak tables, then explain what the results mean.",
                "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "process_uploaded_files_batch",
                "description": "Process every uploaded Excel file in one batch workflow. For each file, inspect/validate, standardize, run T2 inversion, optionally run Gaussian peaks, interpret results, and generate a report in a separate output folder.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "run_gaussian": {
                            "type": "boolean",
                            "description": "Whether to run Gaussian peak decomposition after inversion. Default: false unless the user asks for peaks.",
                        },
                        "peak_count": {"type": "integer", "description": "Number of Gaussian peaks when run_gaussian is true. Default: 2.", "minimum": 1, "maximum": 8},
                        "regularization": {
                            "type": "number",
                            "description": "Optional fixed smoothing/regularization factor. Omit this to use L-curve automatically for every file.",
                        },
                        "t2_min_ms": {"type": "number", "description": "Lower bound for the T2 search range. Default: 0.01 ms for L-curve."},
                        "t2_max_ms": {"type": "number", "description": "Upper bound for the T2 search range. Default: 100000 ms for L-curve."},
                        "num_bins": {"type": "integer", "description": "Number of T2 bins. Default: 200."},
                        "alpha_count": {"type": "integer", "description": "Number of L-curve smoothing factors. Default: 60."},
                    },
                    "required": [],
                    "additionalProperties": False,
                },
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


def _is_english(language: str) -> bool:
    return language.lower().startswith("english")


def _language_name(language: str) -> str:
    return "English" if _is_english(language) else "Chinese"


def _safe_batch_folder(path: Path) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.name).strip("._")
    return token or "uploaded_file"


def _uploaded_paths(context: AgentRuntimeContext) -> list[Path]:
    paths = list(context.uploaded_paths)
    if context.uploaded_path is not None and context.uploaded_path not in paths:
        paths.insert(0, context.uploaded_path)
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = str(Path(path))
        if resolved not in seen:
            seen.add(resolved)
            unique.append(Path(path))
    return unique


def _require_upload(context: AgentRuntimeContext, response_language: str = "中文") -> AgentToolResult | None:
    if context.uploaded_path is None:
        message = "No Excel file has been uploaded yet. Please upload data before asking me to inspect or run it." if _is_english(response_language) else "还没有上传 Excel 文件。请先上传数据，再让我检查或运行。"
        return AgentToolResult("failed", message, error="missing_upload")
    return None


def _is_gaussian_only_goal(context: AgentRuntimeContext) -> bool:
    return infer_requested_plan(context.last_user_goal).workflow == "gaussian_only"


def _gaussian_only_requires_spectrum_error(response_language: str) -> AgentToolResult:
    message = (
        "You asked for peak decomposition only, so I will not run T2 inversion automatically. Please upload an existing T2 spectrum, or explicitly confirm that you want me to run inversion first and then decompose peaks."
        if _is_english(response_language)
        else "你要求只做分峰，所以我不会自动先做 T2 反演。请上传已有 T2 谱表，或明确确认要我先反演再分峰。"
    )
    return AgentToolResult("failed", message, error="gaussian_only_requires_spectrum")


def process_uploaded_files_batch(args: dict[str, Any], context: AgentRuntimeContext, response_language: str = "中文") -> AgentToolResult:
    """Run a complete conservative workflow for every uploaded workbook."""

    uploaded_paths = _uploaded_paths(context)
    if not uploaded_paths:
        message = "No Excel files have been uploaded yet." if _is_english(response_language) else "还没有上传 Excel 文件。"
        return AgentToolResult("failed", message, error="missing_upload")

    run_gaussian = bool(args.get("run_gaussian", False))
    peak_count = int(args.get("peak_count", 2))
    fixed_regularization = args.get("regularization")
    batch_root = context.workspace / "batch_results"
    batch_root.mkdir(parents=True, exist_ok=True)

    artifacts: list[str] = []
    rows: list[dict[str, Any]] = []
    successful_files = 0

    for uploaded_path in uploaded_paths:
        file_dir = batch_root / _safe_batch_folder(uploaded_path)
        file_dir.mkdir(parents=True, exist_ok=True)
        file_results: list[AgentToolResult] = []
        row: dict[str, Any] = {
            "file": Path(uploaded_path).name,
            "folder": str(file_dir),
            "status": "failed",
            "steps": [],
            "artifacts": [],
        }

        validation = validate_workbook(uploaded_path, language=response_language)
        row["steps"].append({"name": "validate_workbook", "status": validation.status, "message": validation.message, "error": validation.error})
        if validation.status != "success":
            rows.append(row)
            continue

        scale = validation.summary.get("recommended_time_to_ms_scale", 1.0)
        repaired = repair_workbook(uploaded_path, file_dir / "standardized", float(scale or 1.0), language=response_language)
        file_results.append(repaired)
        row["steps"].append({"name": "repair_workbook", "status": repaired.status, "message": repaired.message, "error": repaired.error})
        artifacts.extend(repaired.artifacts)
        row["artifacts"].extend(repaired.artifacts)
        if repaired.status != "success" or not repaired.artifacts:
            rows.append(row)
            continue

        if fixed_regularization is not None:
            inversion_params = {
                "time_to_ms_scale": 1.0,
                "regularization": float(fixed_regularization),
                "t2_min_ms": float(args.get("t2_min_ms", 1.0)),
                "t2_max_ms": float(args.get("t2_max_ms", 1e4)),
                "num_bins": int(args.get("num_bins", 200)),
            }
            inversion = run_fixed_nnls(Path(repaired.artifacts[0]), file_dir / "nnls", inversion_params, language=response_language)
            step_name = "run_fixed_nnls"
        else:
            inversion_params = {
                "time_to_ms_scale": 1.0,
                "t2_min_ms": float(args.get("t2_min_ms", 1e-2)),
                "t2_max_ms": float(args.get("t2_max_ms", 1e5)),
                "num_bins": int(args.get("num_bins", 200)),
                "alpha_count": int(args.get("alpha_count", 60)),
            }
            inversion = run_lcurve(Path(repaired.artifacts[0]), file_dir / "lcurve", inversion_params, language=response_language)
            step_name = "run_lcurve"

        file_results.append(inversion)
        row["steps"].append({"name": step_name, "status": inversion.status, "message": inversion.message, "error": inversion.error})
        artifacts.extend(inversion.artifacts)
        row["artifacts"].extend(inversion.artifacts)
        if inversion.status != "success":
            rows.append(row)
            continue

        spectrum_path = inversion.summary.get("spectrum_xlsx")
        if run_gaussian and spectrum_path:
            gaussian = run_gaussian_peaks(Path(spectrum_path), file_dir / "gaussian", {"peak_count": peak_count}, language=response_language)
            file_results.append(gaussian)
            row["steps"].append({"name": "run_gaussian_peaks", "status": gaussian.status, "message": gaussian.message, "error": gaussian.error})
            artifacts.extend(gaussian.artifacts)
            row["artifacts"].extend(gaussian.artifacts)

        interpretation = interpret_results(file_results, file_dir / "interpretation", language=response_language)
        file_results.append(interpretation)
        row["steps"].append({"name": "interpret_results", "status": interpretation.status, "message": interpretation.message, "error": interpretation.error})
        artifacts.extend(interpretation.artifacts)
        row["artifacts"].extend(interpretation.artifacts)

        plan = infer_requested_plan(context.last_user_goal)
        plan.needs_gaussian = run_gaussian
        plan.peak_count = peak_count
        report = generate_report(
            file_dir / "report",
            user_goal=context.last_user_goal or ("Batch T2 processing" if _is_english(response_language) else "批量 T2 数据处理"),
            validation=validation,
            workflow_results=file_results,
            parameter_notes=build_parameter_guidance(plan, language=response_language),
            language=response_language,
        )
        row["steps"].append({"name": "generate_report", "status": report.status, "message": report.message, "error": report.error})
        artifacts.extend(report.artifacts)
        row["artifacts"].extend(report.artifacts)
        row["status"] = "success" if report.status == "success" else "partial"
        successful_files += 1 if row["status"] in {"success", "partial"} else 0
        rows.append(row)

    summary_path = batch_root / "batch_summary.md"
    if _is_english(response_language):
        lines = ["# Batch T2 Processing Summary", ""]
        for row in rows:
            lines.extend([f"## {row['file']}", f"- Status: {row['status']}", f"- Output folder: `{row['folder']}`"])
            for step in row["steps"]:
                lines.append(f"- {step['name']}: {step['status']} - {step['message']}")
            lines.append("")
        message = f"Batch processing completed for {successful_files}/{len(uploaded_paths)} file(s). Results are grouped by file folder in the download zip."
    else:
        lines = ["# 批量 T2 处理摘要", ""]
        for row in rows:
            lines.extend([f"## {row['file']}", f"- 状态：{row['status']}", f"- 输出文件夹：`{row['folder']}`"])
            for step in row["steps"]:
                lines.append(f"- {step['name']}：{step['status']} - {step['message']}")
            lines.append("")
        message = f"批量处理完成：{successful_files}/{len(uploaded_paths)} 个文件已生成结果。下载 zip 会按文件夹分组保存每个文件的产物。"

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    artifacts.append(str(summary_path))

    status = "success" if successful_files == len(uploaded_paths) else ("failed" if successful_files == 0 else "success")
    return AgentToolResult(
        status,
        message,
        artifacts=artifacts,
        summary={
            "file_count": len(uploaded_paths),
            "successful_file_count": successful_files,
            "batch_root": str(batch_root),
            "files": rows,
        },
        error=None if successful_files else "batch_failed",
    )


def execute_agent_tool(name: str, args: dict[str, Any], context: AgentRuntimeContext, response_language: str = "中文") -> AgentToolResult:
    """Execute one whitelisted tool and update runtime context."""

    if name == "process_uploaded_files_batch":
        result = process_uploaded_files_batch(args, context, response_language=response_language)
        context.results.append(result)
        return result

    if name in {"inspect_workbook_schema", "validate_workbook", "repair_workbook"}:
        missing = _require_upload(context, response_language)
        if missing:
            return missing

    if name in {"repair_workbook", "run_lcurve", "run_fixed_nnls"} and _is_gaussian_only_goal(context):
        if context.validation is None or context.validation.summary.get("data_kind") != "spectrum":
            return _gaussian_only_requires_spectrum_error(response_language)

    if name in {"run_lcurve", "run_fixed_nnls"} and context.validation is not None and context.validation.summary.get("data_kind") == "spectrum":
        message = "The uploaded workbook looks like an existing T2 spectrum, so I will not run inversion on it. Use run_gaussian_peaks directly if the user wants peak decomposition." if _is_english(response_language) else "上传的工作簿看起来是已有 T2 谱表，因此不会再做反演。如果用户要分峰，请直接调用 run_gaussian_peaks。"
        return AgentToolResult("failed", message, error="spectrum_input_not_decay")

    if name in {"run_lcurve", "run_fixed_nnls"} and context.repaired_path is None:
        message = "Before inversion, repair_workbook must generate a standardized Excel file." if _is_english(response_language) else "反演前需要先调用 repair_workbook 生成标准化 Excel。"
        return AgentToolResult("failed", message, error="missing_repaired_workbook")

    if name == "inspect_workbook_schema":
        return inspect_workbook_schema(context.uploaded_path, int(args.get("preview_rows", 8)), language=response_language)  # type: ignore[arg-type]

    if name == "validate_workbook":
        result = validate_workbook(context.uploaded_path, language=response_language)  # type: ignore[arg-type]
        context.validation = result
        if result.status == "success" and result.summary.get("data_kind") == "spectrum":
            context.spectrum_path = Path(context.uploaded_path)  # type: ignore[arg-type]
            context.repaired_path = None
        return result

    if name == "repair_workbook":
        if context.validation is not None and context.validation.summary.get("data_kind") == "spectrum":
            message = "The uploaded workbook already looks like a T2 spectrum, so it should not be standardized as raw decay data. Continue with run_gaussian_peaks if the user wants peak decomposition." if _is_english(response_language) else "上传的工作簿已经像是 T2 谱表，不应标准化成原始衰减数据。如果用户要分峰，请继续调用 run_gaussian_peaks。"
            return AgentToolResult("failed", message, error="spectrum_input_not_decay")
        scale = args.get("time_to_ms_scale")
        if scale is None and context.validation is not None:
            scale = context.validation.summary.get("recommended_time_to_ms_scale", 1.0)
        result = repair_workbook(context.uploaded_path, context.workspace / "standardized", float(scale or 1.0), language=response_language)  # type: ignore[arg-type]
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
        result = run_lcurve(context.repaired_path, context.workspace / "lcurve", params, language=response_language)  # type: ignore[arg-type]
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
        result = run_fixed_nnls(context.repaired_path, context.workspace / "nnls", params, language=response_language)  # type: ignore[arg-type]
        context.results.append(result)
        if result.status == "success" and "spectrum_xlsx" in result.summary:
            context.spectrum_path = Path(result.summary["spectrum_xlsx"])
        return result

    if name == "plot_decay_spectrum":
        if context.repaired_path is None or context.spectrum_path is None:
            message = "Plotting requires both a standardized decay file and a T2 spectrum file." if _is_english(response_language) else "画图前需要已有标准化 decay 文件和 T2 spectrum 文件。"
            return AgentToolResult("failed", message, error="missing_plot_inputs")
        result = plot_decay_spectrum(context.repaired_path, context.spectrum_path, context.workspace / "plots", {"time_to_ms_scale": 1.0}, language=response_language)
        context.results.append(result)
        return result

    if name == "run_gaussian_peaks":
        if context.spectrum_path is None:
            message = "Peak decomposition requires a completed T2 inversion or an uploaded T2 spectrum." if _is_english(response_language) else "分峰前需要先完成 T2 反演或上传 T2 spectrum。"
            return AgentToolResult("failed", message, error="missing_spectrum")
        result = run_gaussian_peaks(context.spectrum_path, context.workspace / "gaussian", {"peak_count": int(args["peak_count"])}, language=response_language)
        context.results.append(result)
        return result

    if name == "generate_report":
        goal = context.last_user_goal or ("The user wants the agent to complete T2 data processing automatically." if _is_english(response_language) else "用户希望由 Agent 自动完成 T2 数据处理。")
        plan = infer_requested_plan(goal)
        result = generate_report(
            context.workspace / "report",
            user_goal=goal,
            validation=context.validation
            or AgentToolResult(
                "failed",
                "Data diagnosis has not been completed yet." if _is_english(response_language) else "尚未完成数据诊断。",
                error="missing_validation",
            ),
            workflow_results=context.results,
            parameter_notes=build_parameter_guidance(plan, language=response_language),
            language=response_language,
        )
        context.report = result
        return result

    if name == "interpret_results":
        result = interpret_results(context.results, context.workspace / "interpretation", language=response_language)
        context.results.append(result)
        return result

    message = f"Unknown tool: {name}" if _is_english(response_language) else f"未知工具：{name}"
    return AgentToolResult("failed", message, error="unknown_tool")


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
    user_language = _language_name(response_language)
    language_instruction = (
        "User-facing language: English. Reply in English. Any visible summaries, explanations, tool-result interpretation, and generated reports must be in English unless the user explicitly asks for another language."
        if _is_english(response_language)
        else "用户可见语言：中文。请用中文回复。所有面向用户的摘要、解释、工具结果解读和生成报告都必须使用中文，除非用户明确要求其他语言。"
    )
    system_content = (
        "You are an NMR T2 inversion agent that can call real tools. "
        "When the user has uploaded data and asks to inspect, run, or interpret it, first call inspect_workbook_schema, then call validate_workbook. "
        "If the user only asks about capabilities, parameter meanings, boundaries, expected data format, workflow, or usage advice, do not call tools; answer clearly. "
        "Do not assume the first column is time. Infer the time/T2 column from labels, monotonicity, numeric ranges, and preview rows. "
        "If the user asks to only run peak decomposition, do not call repair_workbook, run_lcurve, or run_fixed_nnls; use an existing/uploaded T2 spectrum, or ask the user to confirm inversion first. "
        "After validate_workbook, check summary.data_kind. If it is spectrum, do not call repair_workbook, run_lcurve, or run_fixed_nnls; ask whether the user wants Gaussian peak decomposition, or call run_gaussian_peaks directly when the user already asked for peaks. "
        "Only run T2 inversion when summary.data_kind is decay. "
        "If Time is in the second column and Peak is in the first column, this is usually a column-order mismatch with the older tool expectation; do not call it swapped labels. "
        "Only say labels may be wrong when labels and numeric shapes contradict each other. "
        "If the column order, header position, multi-signal layout, or workbook layout is nonstandard, tell the user and call repair_workbook to standardize it. "
        "When the user does not understand parameters and the uploaded data is decay data, prefer repair_workbook + run_lcurve. "
        "When multiple files are uploaded and the user asks to process all files, batch process files, analyze multiple files, or generate results for all uploads, call process_uploaded_files_batch instead of running single-file tools repeatedly. "
        "When the user explicitly specifies a smoothing/regularization factor, use run_fixed_nnls. "
        "When the user asks for peak decomposition, call run_gaussian_peaks after a spectrum exists. "
        "When the user asks to interpret results, asks what the result means, asks whether the result is good, or asks for next steps, call interpret_results instead of only pointing to the right-side tool results. "
        "Do not claim that a tool has run unless this turn includes the corresponding tool result. "
        "Write for beginners and explain the role of the smoothing factor, L-curve, T2 range, and peak count when relevant. "
        f"{language_instruction} "
        f"Requested user-facing language label: {user_language}."
        f"\n\n{render_skill_prompt()}"
    )
    system_index = next((idx for idx, message in enumerate(messages) if message.get("role") == "system"), None)
    if system_index is None:
        messages.insert(
            0,
            {
                "role": "system",
                "content": system_content,
            },
        )
    else:
        messages[system_index] = {**messages[system_index], "content": system_content}

    messages.append({"role": "user", "content": user_message})
    tool_results: list[AgentToolResult] = []
    trace: list[dict[str, Any]] = [
        {
            "kind": "plan",
            "message": "This turn first lets the model decide whether tools are needed; if tools are requested, only whitelisted T2 tools are executed."
            if _is_english(response_language)
            else "本轮先让模型判断是否需要调用工具；若模型请求工具，只执行白名单 T2 tools。",
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
                    "message": f"AI requested tool `{name}`." if _is_english(response_language) else f"AI 请求调用工具 `{name}`。",
                }
            )
            if on_trace:
                on_trace(trace[-1])
            result = execute_agent_tool(name, args, context, response_language=response_language)
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

    fallback = (
        "I called several rounds of tools but did not receive a final assistant reply yet. Please check the tool results on the right, or ask me to continue the analysis."
        if _is_english(response_language)
        else "我已经调用了多轮工具，但还没有得到最终回复。请查看右侧工具结果，或让我继续分析。"
    )
    return AgentTurnResult(fallback, messages, tool_results, trace)
