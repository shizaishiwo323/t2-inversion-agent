"""Rule-based parameter guidance used with or without DeepSeek."""

from __future__ import annotations

import re

from .models import UserWorkflowPlan


CN_NUMBER_MAP = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
}


def _extract_peak_count(text: str) -> int | None:
    match = re.search(r"(?:分|拆|拟合)?\s*(\d+)\s*(?:个)?\s*峰", text)
    if match:
        return max(1, int(match.group(1)))

    for token, value in CN_NUMBER_MAP.items():
        if re.search(fr"(?:分|拆|拟合)?\s*{token}\s*(?:个)?\s*峰", text):
            return value
    return None


def _extract_regularization(text: str) -> float | None:
    patterns = (
        r"(?:平滑因子|正则化因子|regularization|alpha|eps)\s*(?:=|为|是|设为|固定为|固定)?\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
        r"固定\s*(?:平滑因子|正则化因子)?\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def infer_requested_plan(user_text: str) -> UserWorkflowPlan:
    """Infer a conservative processing plan from natural-language intent."""

    text = (user_text or "").strip()
    lowered = text.lower()

    plan = UserWorkflowPlan()
    plan.user_is_unsure = any(token in text for token in ("不懂", "不知道", "默认", "推荐", "你来", "自动"))

    regularization = _extract_regularization(text)
    if regularization is not None:
        plan.workflow = "fixed_nnls"
        plan.regularization = regularization
        plan.user_is_unsure = False

    peak_count = _extract_peak_count(text)
    if peak_count is not None:
        plan.needs_gaussian = True
        plan.peak_count = peak_count
        if plan.workflow == "lcurve_inversion" and any(token in text for token in ("已有", "谱", "spectrum")):
            plan.workflow = "gaussian_only"
    elif any(token in lowered for token in ("gaussian", "peak", "分峰", "峰")):
        plan.needs_gaussian = True
        plan.peak_count = 2

    if any(token in text for token in ("全流程", "都做", "反演并分峰", "反演和分峰")):
        plan.workflow = "full_analysis"
        plan.needs_gaussian = True

    if any(token in text for token in ("l曲线", "L曲线", "l-curve", "L-curve", "自动平滑")):
        plan.workflow = "lcurve_inversion"

    return plan


def build_parameter_guidance(plan: UserWorkflowPlan) -> str:
    """Return user-facing Chinese guidance for the inferred plan."""

    lines = [
        "我会先解释关键参数，再给出推荐方案：",
        "",
        "- 平滑因子/正则化因子：控制 T2 谱的平滑程度。值越小，结果越贴近原始数据，但更容易把噪声变成假峰；值越大，谱线越平滑，但可能把真实的小峰抹掉。",
        "- L-curve：自动在“拟合误差”和“谱线平滑”之间找折中点，适合还不知道该选多大平滑因子的用户。",
        "- T2 范围：决定反演搜索哪些弛豫时间。范围太窄可能漏峰，范围太宽会增加不稳定性。默认范围适合先做探索性分析。",
        "- 分峰数量：把 T2 谱拆成几个 Gaussian 峰，用来近似解释不同孔隙或流体组分。峰数不是越多越好，太多容易过拟合。",
        "",
    ]

    if plan.workflow == "fixed_nnls":
        lines.append(f"你已经指定固定平滑因子 {plan.regularization:g}，我会使用固定 NNLS 反演，并在报告里提示它可能比 L-curve 更依赖人工经验。")
    elif plan.workflow == "gaussian_only":
        lines.append("你更像是要对已有 T2 谱做分峰解释。我会跳过 decay 反演，直接进入 Gaussian 分峰。")
    else:
        lines.append("默认推荐：使用 L-curve 自动选择平滑因子。这样对新手更稳妥，也能减少人工调参带来的主观性。")

    if plan.needs_gaussian:
        lines.append(f"分峰推荐：按你的需求使用 {plan.peak_count} 个峰。运行后我会报告每个峰的位置、面积比例和拟合图。")
    else:
        lines.append("分峰默认不自动开启。先得到 T2 谱后，如果你要解释孔隙/流体组分，再选择 2 到 3 个峰开始比较合适。")

    return "\n".join(lines)
