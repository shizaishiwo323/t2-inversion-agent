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
    response_language: str = "中文",
) -> str:
    """Generate an assistant reply, falling back to deterministic guidance."""

    fallback = build_parameter_guidance(plan, language=response_language)
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
                        "You are an NMR T2 inversion agent. Explain parameters, recommend conservative defaults, "
                        "and guide the user through key decisions. Do not ask the user to run shell commands, "
                        "and do not invent results that have not been produced. Computation can only be done "
                        "by these web app tools: validate_workbook, repair_workbook, run_lcurve, "
                        "run_fixed_nnls, plot_decay_spectrum, run_gaussian_peaks, generate_report. "
                        f"User-facing output language: {response_language}."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"User message: {user_message}\n"
                        f"Data diagnosis: {validation_message}\n"
                        f"Current plan: {plan}\n"
                        "Briefly explain the parameters and recommend the next step in the requested user-facing language."
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
