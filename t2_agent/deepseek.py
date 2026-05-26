"""DeepSeek chat helper for parameter guidance."""

from __future__ import annotations

import os
from typing import Any

from .guidance import build_parameter_guidance
from .models import UserWorkflowPlan


DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def get_deepseek_api_key(secrets: Any | None = None) -> str | None:
    """Read API key from Streamlit secrets first, then environment."""

    if secrets is not None:
        try:
            value = secrets.get("DEEPSEEK_API_KEY")
            if value:
                return str(value)
        except Exception:
            pass
    return os.getenv("DEEPSEEK_API_KEY")


def build_agent_reply(
    *,
    user_message: str,
    plan: UserWorkflowPlan,
    validation_message: str,
    model: str,
    thinking_enabled: bool,
    api_key: str | None,
) -> str:
    """Generate an assistant reply, falling back to deterministic guidance."""

    fallback = build_parameter_guidance(plan)
    if not api_key:
        return fallback

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        extra_body = {"thinking": {"type": "enabled" if thinking_enabled else "disabled"}}
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是 NMR T2 反演智能体。你的职责是解释参数、推荐保守默认值、"
                        "引导用户确认关键节点。你不能要求执行 shell 命令，不能编造已经运行的结果。"
                        "计算只能由网页端白名单工具完成：validate_workbook, repair_workbook, "
                        "run_lcurve, run_fixed_nnls, plot_decay_spectrum, run_gaussian_peaks, generate_report。"
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"用户消息：{user_message}\n"
                        f"数据诊断：{validation_message}\n"
                        f"当前计划：{plan}\n"
                        "请用中文简洁解释参数，并告诉用户推荐下一步。"
                    ),
                },
            ],
            extra_body=extra_body,
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return content.strip() if content else fallback
    except Exception as exc:
        return f"{fallback}\n\n（DeepSeek 暂时不可用，已使用本地规则引导。错误：{exc}）"
