from __future__ import annotations

import io
import html
import re
import zipfile
from pathlib import Path
from typing import Any
from uuid import uuid4

import pandas as pd
import streamlit as st

from t2_agent.agent import AgentRuntimeContext, run_deepseek_agent_turn
from t2_agent.deepseek import get_deepseek_api_key
from t2_agent.i18n import t
from t2_agent.interactive_lcurve import alpha_path_figure, lcurve_metric_figure, selected_alpha_from_plotly_selection, t2_spectrum_figure
from t2_agent.models import AgentToolResult
from t2_agent.tools import run_fixed_nnls


APP_ROOT = Path(__file__).resolve().parent
RUNS_ROOT = APP_ROOT / "runs"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
TABLE_SUFFIXES = {".xlsx", ".xls", ".csv"}
REPORT_SUFFIXES = {".md", ".txt"}
SIMULATION_STAGE_ORDER = ["geometry", "mesh", "decay", "inversion", "gaussian", "report"]
MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
REPORT_ANALYSIS_START = "<!-- conversation-analysis:start -->"
REPORT_ANALYSIS_END = "<!-- conversation-analysis:end -->"
AVAILABLE_MODELS = ["deepseek-v4-flash", "deepseek-v4-pro"]
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_THINKING_ENABLED = True
INTRO_QUERY_KEY = "hide_t2_agent_intro"


WELCOME_MESSAGES = {
    "中文": """你好，我是 **T2 反演智能体**。我可以帮你把 NMR T2 衰减数据从“表格”处理成可解释的 T2 谱和报告。

我能做的事：

- 检查 Excel 数据格式，识别时间列、信号列、空列、列顺序不符合工具预期等问题
- 自动整理表格为 `time_ms + signal` 标准格式
- 做 T2 反演：默认用 L-curve 自动选择平滑因子，也支持你指定固定平滑因子
- 生成衰减曲线、T2 谱图、L-curve 图
- 对 T2 谱做 Gaussian 分峰，并解释峰位置和面积比例
- 做二维 NMR 模拟：规则几何或红黄白 PNG 相图 -> pyGIMLi 网格 -> T2 衰减 -> T2 反演
- 仍然支持只做 T2 反演，不需要先跑模拟
- 读取已经生成的结果，解释这个结果说明什么，并给出下一步建议

我现在的边界：

- 专注 2D NMR 模拟、T2 decay / T2 spectrum 数据处理
- 第一版模拟仅支持 2D；不做 CT 分割、3D、T2-T2 或 D-T2
- 不替代专业判断，结果解释需要结合样品背景

你可以先问我：

- `你完整能做什么？参数边界是什么？`
- `我的 Excel 应该是什么格式？`
- `什么是平滑因子？L-curve 是干嘛的？`
- `我不懂参数，应该怎么开始？`

准备好后再上传 Excel，并告诉我你的目标。"""
    ,
    "English": """Hi, I am the **T2 Inversion Agent**. I help turn NMR T2 decay spreadsheets into interpretable T2 spectra, figures, and reports.

What I can do:

- Inspect Excel layouts and identify time columns, signal columns, blank columns, and column order issues
- Normalize tables into a `time_ms + signal` format
- Run T2 inversion: L-curve by default, or fixed regularization when you provide a smoothing factor
- Generate decay plots, T2 spectrum plots, and L-curve figures
- Run Gaussian peak decomposition and explain peak positions and area fractions
- Run first-version 2D NMR simulation: rule geometry or red/yellow/white PNG phase map -> pyGIMLi mesh -> T2 decay -> T2 inversion
- Still support standalone T2 inversion without a simulation step
- Read generated results and explain what they mean, with suggestions for next steps

Current boundaries:

- Focused on 2D NMR simulation, T2 decay, and T2 spectrum processing
- First-version simulation supports 2D only; it does not perform CT segmentation, 3D simulation, T2-T2, or D-T2
- Does not replace domain judgment; interpretation still depends on sample context

You can ask first:

- `What can you do? What are your parameter boundaries?`
- `What should my Excel file look like?`
- `What is a smoothing factor? What does L-curve do?`
- `I do not understand the parameters. How should I start?`

When you are ready, upload an Excel file and tell me your goal.""",
}


def welcome_message(language: str) -> str:
    return WELCOME_MESSAGES.get(language, WELCOME_MESSAGES["中文"])


def init_state() -> None:
    defaults = {
        "workspace": None,
        "uploaded_path": None,
        "uploaded_paths": [],
        "loaded_active_uploaded_path": None,
        "file_contexts": {},
        "file_agent_messages": {},
        "file_display_messages": {},
        "file_display_traces": {},
        "file_display_artifacts": {},
        "file_zip_bytes": {},
        "file_welcome_language": {},
        "agent_context": None,
        "agent_messages": [],
        "display_messages": [],
        "display_traces": [],
        "display_artifacts": [],
        "language": "中文",
        "welcome_language": "中文",
        "intro_seen": False,
        "intro_suppressed": False,
        "zip_bytes": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if query_param_enabled(INTRO_QUERY_KEY):
        st.session_state.intro_suppressed = True
    if not st.session_state.display_messages:
        st.session_state.display_messages = []
        st.session_state.welcome_language = st.session_state.language
        st.session_state.display_traces = []
        st.session_state.display_artifacts = []
    strip_seed_welcome_messages()
    align_display_artifacts()


def query_param_enabled(key: str) -> bool:
    value = st.query_params.get(key)
    if isinstance(value, list):
        value = value[-1] if value else None
    return str(value).lower() in {"1", "true", "yes", "on"}


def clear_query_param(key: str) -> None:
    if key in st.query_params:
        del st.query_params[key]


def strip_seed_welcome_messages() -> None:
    """Remove the old in-chat welcome now that onboarding lives in the modal."""

    messages = list(st.session_state.get("display_messages", []))
    traces = list(st.session_state.get("display_traces", []))
    artifacts = list(st.session_state.get("display_artifacts", []))
    if not messages:
        return

    kept_messages: list[tuple[str, str]] = []
    kept_traces: list[list[dict]] = []
    kept_artifacts: list[list[str]] = []
    changed = False
    for idx, message in enumerate(messages):
        role, content = message
        if role == "assistant" and content in WELCOME_MESSAGES.values():
            changed = True
            continue
        kept_messages.append(message)
        kept_traces.append(traces[idx] if idx < len(traces) else [])
        kept_artifacts.append(artifacts[idx] if idx < len(artifacts) else [])

    if changed:
        st.session_state.display_messages = kept_messages
        st.session_state.display_traces = kept_traces
        st.session_state.display_artifacts = kept_artifacts


def align_display_artifacts() -> None:
    """Keep per-message artifact metadata aligned with visible chat messages."""

    messages = st.session_state.get("display_messages", [])
    artifacts = st.session_state.get("display_artifacts", [])
    if len(artifacts) < len(messages):
        artifacts = [*artifacts, *([[]] * (len(messages) - len(artifacts)))]
    elif len(artifacts) > len(messages):
        artifacts = artifacts[: len(messages)]
    st.session_state.display_artifacts = artifacts


def sync_language_seed_messages() -> None:
    """Refresh built-in assistant seed messages after the UI language changes."""

    language = st.session_state.get("language", "中文")
    previous_language = st.session_state.get("welcome_language", "中文")
    if language == previous_language:
        return

    messages = st.session_state.get("display_messages", [])
    for idx, (role, content) in enumerate(messages):
        if role != "assistant":
            continue
        if content in {t("中文", "upload_received"), t("English", "upload_received")}:
            messages[idx] = ("assistant", t(language, "upload_received"))

    st.session_state.display_messages = messages
    st.session_state.welcome_language = language
    active_path = st.session_state.get("loaded_active_uploaded_path")
    if active_path:
        st.session_state.file_display_messages[active_path] = messages
        st.session_state.file_welcome_language[active_path] = language
        st.session_state.file_display_artifacts[active_path] = st.session_state.display_artifacts


def ensure_workspace() -> Path:
    if st.session_state.workspace is None:
        workspace = RUNS_ROOT / uuid4().hex
        workspace.mkdir(parents=True, exist_ok=True)
        st.session_state.workspace = str(workspace)
    return Path(st.session_state.workspace)


def safe_upload_key(path: Path) -> str:
    token = re.sub(r"[^A-Za-z0-9_.-]+", "_", path.name).strip("._")
    return token or "uploaded_file"


def save_upload(uploaded_file) -> Path:
    workspace = ensure_workspace()
    upload_dir = workspace / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_path = upload_dir / uploaded_file.name
    output_path.write_bytes(uploaded_file.getbuffer())
    return output_path


def make_file_workspace(uploaded_path: Path) -> Path:
    workspace = ensure_workspace() / "tasks" / safe_upload_key(uploaded_path)
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def default_file_display_state(language: str) -> tuple[list[tuple[str, str]], list[list[dict]]]:
    return [
        ("assistant", t(language, "upload_received")),
    ], [[]]


def ensure_file_state(uploaded_path: Path) -> None:
    path_key = str(uploaded_path)
    contexts = st.session_state.file_contexts
    if path_key not in contexts:
        contexts[path_key] = AgentRuntimeContext(
            workspace=make_file_workspace(uploaded_path),
            uploaded_path=uploaded_path,
            uploaded_paths=[uploaded_path],
        )
    if path_key not in st.session_state.file_agent_messages:
        st.session_state.file_agent_messages[path_key] = []
    if path_key not in st.session_state.file_display_messages:
        messages, traces = default_file_display_state(st.session_state.language)
        st.session_state.file_display_messages[path_key] = messages
        st.session_state.file_display_traces[path_key] = traces
        st.session_state.file_display_artifacts[path_key] = [[] for _ in messages]
        st.session_state.file_welcome_language[path_key] = st.session_state.language
    if path_key not in st.session_state.file_zip_bytes:
        st.session_state.file_zip_bytes[path_key] = None


def save_current_file_state(path_key: str | None = None) -> None:
    path_key = path_key or st.session_state.get("loaded_active_uploaded_path")
    if not path_key:
        return
    if st.session_state.agent_context is not None:
        st.session_state.file_contexts[path_key] = st.session_state.agent_context
    st.session_state.file_agent_messages[path_key] = st.session_state.agent_messages
    st.session_state.file_display_messages[path_key] = st.session_state.display_messages
    st.session_state.file_display_traces[path_key] = st.session_state.display_traces
    st.session_state.file_display_artifacts[path_key] = st.session_state.display_artifacts
    st.session_state.file_zip_bytes[path_key] = st.session_state.zip_bytes
    st.session_state.file_welcome_language[path_key] = st.session_state.welcome_language


def activate_uploaded_path(uploaded_path: Path | None) -> None:
    previous_key = st.session_state.get("loaded_active_uploaded_path")
    if previous_key == (str(uploaded_path) if uploaded_path else None):
        return

    save_current_file_state(previous_key)
    if uploaded_path is None:
        st.session_state.uploaded_path = None
        st.session_state.agent_context = None
        st.session_state.agent_messages = []
        st.session_state.display_messages = []
        st.session_state.display_traces = []
        st.session_state.display_artifacts = []
        st.session_state.zip_bytes = None
        st.session_state.welcome_language = st.session_state.language
        st.session_state.loaded_active_uploaded_path = None
        return

    ensure_file_state(uploaded_path)
    path_key = str(uploaded_path)
    st.session_state.file_contexts[path_key].uploaded_paths = [Path(path) for path in st.session_state.get("uploaded_paths", [path_key])]
    st.session_state.uploaded_path = path_key
    st.session_state.agent_context = st.session_state.file_contexts[path_key]
    st.session_state.agent_messages = st.session_state.file_agent_messages[path_key]
    st.session_state.display_messages = st.session_state.file_display_messages[path_key]
    st.session_state.display_traces = st.session_state.file_display_traces[path_key]
    st.session_state.display_artifacts = st.session_state.file_display_artifacts.get(
        path_key, [[] for _ in st.session_state.display_messages]
    )
    align_display_artifacts()
    st.session_state.zip_bytes = st.session_state.file_zip_bytes.get(path_key)
    st.session_state.welcome_language = st.session_state.file_welcome_language.get(path_key, st.session_state.language)
    st.session_state.loaded_active_uploaded_path = path_key


def register_uploaded_files(uploaded_files: list) -> None:
    if not uploaded_files:
        return

    paths = list(st.session_state.uploaded_paths)
    for uploaded_file in uploaded_files:
        uploaded_path = save_upload(uploaded_file)
        path_key = str(uploaded_path)
        if path_key not in paths:
            paths.append(path_key)
        ensure_file_state(uploaded_path)

    st.session_state.uploaded_paths = paths
    all_paths = [Path(path) for path in paths]
    for context in st.session_state.file_contexts.values():
        context.uploaded_paths = all_paths
    if st.session_state.loaded_active_uploaded_path not in paths:
        activate_uploaded_path(Path(paths[0]))


def collect_artifacts(results: list[AgentToolResult], report: AgentToolResult | None) -> list[Path]:
    paths: list[Path] = []
    for result in results:
        for item in result.artifacts:
            path = Path(item)
            if path.exists() and path.is_file():
                paths.append(path)
    if report:
        for item in report.artifacts:
            path = Path(item)
            if path.exists() and path.is_file():
                paths.append(path)
    return paths


def collect_context_artifacts(context: AgentRuntimeContext) -> list[Path]:
    """Collect artifacts produced across all turns in one task."""

    paths = collect_artifacts(context.tool_history, context.report)
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def resolve_artifact_image_reference(reference: str, artifacts: list[Path]) -> Path | None:
    """Resolve a markdown image target such as `decay_t2` to a generated image."""

    cleaned = reference.strip().strip("\"'").split("#", 1)[0].split("?", 1)[0]
    if not cleaned:
        return None

    direct = Path(cleaned)
    if direct.is_absolute() and direct.exists() and direct.suffix.lower() in IMAGE_SUFFIXES:
        return direct

    normalized = Path(cleaned).name.lower()
    normalized_stem = Path(normalized).stem
    for artifact in artifacts:
        path = Path(artifact)
        if not path.exists() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        name = path.name.lower()
        stem = path.stem.lower()
        if normalized in name or normalized_stem in stem:
            return path
    return None


def group_simulation_stage_artifacts(result: AgentToolResult) -> dict[str, list[Path]]:
    stage_map = result.summary.get("simulation_stages") if result.summary else None
    if not isinstance(stage_map, dict):
        return {}

    grouped: dict[str, list[Path]] = {}
    for stage in SIMULATION_STAGE_ORDER:
        paths = stage_map.get(stage)
        if not isinstance(paths, list):
            continue
        existing = [Path(path) for path in paths if Path(path).exists()]
        if existing:
            grouped[stage] = existing
    return grouped


def render_chat_content(content: str, artifacts: list[Path] | None = None) -> None:
    """Render chat markdown and show referenced generated images inline."""

    artifact_paths = artifacts or []
    cursor = 0
    matched_image = False
    for match in MARKDOWN_IMAGE_RE.finditer(content):
        before = content[cursor : match.start()].strip()
        if before:
            st.markdown(before)
        alt_text, target = match.groups()
        image_path = resolve_artifact_image_reference(target, artifact_paths)
        if image_path is not None:
            st.image(str(image_path), caption=alt_text or image_path.name, width="stretch")
            matched_image = True
        else:
            st.markdown(match.group(0))
        cursor = match.end()

    rest = content[cursor:].strip()
    if rest:
        st.markdown(rest)
    elif not matched_image:
        st.markdown(content)


def make_zip(paths: list[Path]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        seen: set[str] = set()
        for path in paths:
            parts = list(path.parts)
            if "batch_results" in parts:
                arcname = Path(*parts[parts.index("batch_results") :]).as_posix()
            elif "tasks" in parts:
                arcname = Path(*parts[parts.index("tasks") + 1 :]).as_posix()
            else:
                arcname = path.name
            if arcname in seen:
                arcname = f"{path.parent.name}__{path.name}"
            seen.add(arcname)
            archive.write(path, arcname=arcname)
    return buffer.getvalue()


def render_result(result: AgentToolResult) -> None:
    if result.status == "success":
        st.success(result.message)
    else:
        st.error(result.message)
        if result.error:
            st.code(result.error)

    if result.summary:
        language = st.session_state.get("language", "中文")
        with st.expander(t(language, "structured_summary"), expanded=False):
            st.json(result.summary)

    grouped = group_simulation_stage_artifacts(result)
    if grouped:
        language = st.session_state.get("language", "中文")
        for stage, paths in grouped.items():
            with st.expander(t(language, f"simulation_stage_{stage}"), expanded=stage in {"geometry", "mesh", "decay"}):
                for path in paths:
                    if path.suffix.lower() in IMAGE_SUFFIXES:
                        st.image(str(path), caption=path.name, width="stretch")
                    else:
                        st.caption(path.name)
        return

    image_paths = [Path(path) for path in result.artifacts if Path(path).suffix.lower() in IMAGE_SUFFIXES]
    for image_path in image_paths[:6]:
        if image_path.exists():
            st.image(str(image_path), caption=image_path.name, width="stretch")


def should_offer_lcurve_parameter_picker(result: AgentToolResult) -> bool:
    """Return whether a tool result can drive the interactive alpha picker."""

    if result.status != "success":
        return False
    metrics_path = result.summary.get("metrics_xlsx")
    if not metrics_path:
        return False
    return Path(str(metrics_path)).exists()


def selected_alpha_fixed_nnls_params(result: AgentToolResult, selected_alpha: float) -> dict[str, Any]:
    """Build fixed-NNLS parameters from an L-curve run, replacing only alpha."""

    source = result.summary.get("parameters") if isinstance(result.summary.get("parameters"), dict) else {}
    return {
        "regularization": float(selected_alpha),
        "num_bins": int(source.get("num_bins", 200)),
        "t2_min_ms": float(source.get("t2_min_ms", 0.01)),
        "t2_max_ms": float(source.get("t2_max_ms", 100000.0)),
        "time_to_ms_scale": float(source.get("time_to_ms_scale", 1.0)),
        "trim_from_peak": bool(source.get("trim_from_peak", True)),
    }


def _read_lcurve_metric_sheets(metrics_path: Path) -> dict[str, pd.DataFrame]:
    sheets = pd.read_excel(metrics_path, sheet_name=None)
    required = {"alpha_regularization", "residual_norm", "roughness_norm"}
    return {
        name: sheet
        for name, sheet in sheets.items()
        if required.issubset(set(sheet.columns)) and not sheet.empty
    }


def _read_first_excel_sheet(path: Path) -> pd.DataFrame:
    sheets = pd.read_excel(path, sheet_name=None)
    return next(iter(sheets.values()))


def _best_alpha_from_metrics(metrics: pd.DataFrame) -> float:
    if "is_selected" in metrics.columns:
        selected_rows = metrics[metrics["is_selected"].astype(bool)]
        if not selected_rows.empty:
            return float(selected_rows.iloc[0]["alpha_regularization"])
    if "selected" in metrics.columns:
        selected_rows = metrics[metrics["selected"].astype(bool)]
        if not selected_rows.empty:
            return float(selected_rows.iloc[0]["alpha_regularization"])
    return float(metrics.iloc[len(metrics) // 2]["alpha_regularization"])


def _selected_lcurve_index(metrics: pd.DataFrame, selected_alpha: float | None) -> int | None:
    if selected_alpha is None or metrics.empty:
        return None
    alpha_values = pd.to_numeric(metrics["alpha_regularization"], errors="coerce")
    distances = (alpha_values - float(selected_alpha)).abs()
    if distances.isna().all():
        return None
    return int(distances.idxmin())


def lcurve_picker_state_keys(result_index: int) -> dict[str, str]:
    """Return separate widget keys and business-state keys for one L-curve picker."""

    base = f"lcurve-alpha-picker-{result_index}"
    return {
        "base": base,
        "open_button": f"{base}-open-button",
        "open_state": f"{base}-open-state",
    }


def render_lcurve_parameter_picker(context: AgentRuntimeContext, result: AgentToolResult, result_index: int, language: str) -> None:
    if not context.repaired_path or not should_offer_lcurve_parameter_picker(result):
        return

    button_label = "进一步挑选最佳平滑因子" if language == "中文" else "Refine smoothing factor"
    caption = (
        "点击后会打开交互式 L-curve。只有确认后才会按选中的平滑因子重新运行固定 NNLS，并导出静态图表。"
        if language == "中文"
        else "Open the interactive L-curve. Fixed-alpha NNLS runs only after confirmation and exports static artifacts."
    )
    keys = lcurve_picker_state_keys(result_index)
    picker_key = keys["base"]
    open_state_key = keys["open_state"]
    st.caption(caption)
    if st.button(button_label, key=keys["open_button"], width="stretch"):
        st.session_state[open_state_key] = True

    if not st.session_state.get(open_state_key):
        return

    @st.dialog("挑选最佳平滑因子" if language == "中文" else "Select Smoothing Factor", width="large")
    def picker_dialog() -> None:
        metrics_path = Path(str(result.summary["metrics_xlsx"]))
        try:
            metric_sheets = _read_lcurve_metric_sheets(metrics_path)
        except Exception as exc:
            st.error(f"无法读取 L-curve metrics：{exc}" if language == "中文" else f"Could not read L-curve metrics: {exc}")
            return
        if not metric_sheets:
            st.warning("没有找到可用于交互选择的 L-curve 指标表。" if language == "中文" else "No usable L-curve metric sheet was found.")
            return

        sheet_names = list(metric_sheets)
        selected_sheet = st.selectbox(
            "信号列" if language == "中文" else "Signal",
            sheet_names,
            key=f"{picker_key}-sheet",
        )
        metrics = metric_sheets[selected_sheet]
        alpha_state_key = f"{picker_key}-{selected_sheet}-alpha"
        alpha_input_key = f"{picker_key}-{selected_sheet}-alpha-input"
        preview_result_key = f"{picker_key}-{selected_sheet}-preview-result"
        preview_alpha_key = f"{picker_key}-{selected_sheet}-preview-alpha"
        if alpha_state_key not in st.session_state:
            st.session_state[alpha_state_key] = _best_alpha_from_metrics(metrics)

        selected_alpha = float(st.session_state[alpha_state_key])
        selected_index = _selected_lcurve_index(metrics, selected_alpha)
        left, right = st.columns([0.58, 0.42], gap="medium")
        with left:
            selection = st.plotly_chart(
                lcurve_metric_figure(metrics, selected_index=selected_index),
                key=f"{picker_key}-{selected_sheet}-lcurve",
                on_select="rerun",
                selection_mode="points",
                width="stretch",
            )
        clicked_alpha = selected_alpha_from_plotly_selection(selection, metrics)
        if clicked_alpha is not None:
            st.session_state[alpha_state_key] = clicked_alpha
            st.session_state[alpha_input_key] = clicked_alpha
            selected_alpha = clicked_alpha
            selected_index = _selected_lcurve_index(metrics, selected_alpha)

        with right:
            st.plotly_chart(
                alpha_path_figure(metrics, selected_index=selected_index),
                key=f"{picker_key}-{selected_sheet}-alpha-path",
                on_select="ignore",
                width="stretch",
            )

        selected_alpha = float(
            st.number_input(
                "输入平滑因子 alpha 用于预览" if language == "中文" else "Alpha for preview",
                value=float(st.session_state.get(alpha_input_key, selected_alpha)),
                min_value=0.0,
                format="%.6e",
                key=alpha_input_key,
            )
        )
        st.session_state[alpha_state_key] = selected_alpha
        st.success(
            f"当前选择 alpha：{selected_alpha:.6e}"
            if language == "中文"
            else f"Selected alpha: {selected_alpha:.6e}"
        )
        st.caption(
            "先预览该 alpha 的 T2 反演结果；满意后再确认加入正式结果并打包导出。T2 范围、bin 数、trim 等沿用这次 L-curve 设置。"
            if language == "中文"
            else "Preview this alpha's T2 inversion first. Confirm only after the preview looks acceptable. T2 range, bins, and trimming follow this L-curve run."
        )
        preview_label = "预览该平滑因子的反演结果" if language == "中文" else "Preview inversion for this alpha"
        if st.button(preview_label, type="secondary", key=f"{picker_key}-{selected_sheet}-preview-button", width="stretch"):
            params = selected_alpha_fixed_nnls_params(result, selected_alpha)
            output_dir = context.workspace / "alpha_preview_nnls"
            with st.status("正在生成预览反演结果..." if language == "中文" else "Generating preview inversion...", expanded=True) as status:
                preview_result = run_fixed_nnls(context.repaired_path, output_dir, params, language=language)
                st.session_state[preview_result_key] = preview_result
                st.session_state[preview_alpha_key] = selected_alpha
                if preview_result.status == "success":
                    status.update(label="预览反演完成" if language == "中文" else "Preview inversion complete", state="complete")
                else:
                    status.update(label="预览反演失败" if language == "中文" else "Preview inversion failed", state="error")

        preview_result = st.session_state.get(preview_result_key)
        preview_alpha = st.session_state.get(preview_alpha_key)
        preview_matches_current = preview_result is not None and preview_alpha is not None and abs(float(preview_alpha) - float(selected_alpha)) <= max(1e-12, abs(float(selected_alpha)) * 1e-9)
        if preview_result is not None and not preview_matches_current:
            st.info("alpha 已变化，请重新预览后再确认。" if language == "中文" else "Alpha changed. Preview again before confirming.")

        if preview_matches_current:
            if preview_result.status == "success" and preview_result.summary.get("spectrum_xlsx"):
                spectrum_path = Path(str(preview_result.summary["spectrum_xlsx"]))
                if spectrum_path.exists():
                    st.markdown("#### 预览反演结果" if language == "中文" else "#### Preview Inversion Result")
                    preview_spectrum = _read_first_excel_sheet(spectrum_path)
                    st.plotly_chart(
                        t2_spectrum_figure(
                            preview_spectrum,
                            float(preview_alpha),
                            title_prefix="T2 预览" if language == "中文" else "T2 preview",
                        ),
                        key=f"{picker_key}-{selected_sheet}-preview-spectrum",
                        width="stretch",
                    )
            elif preview_result.status != "success":
                st.error(preview_result.message)
                if preview_result.error:
                    st.caption(preview_result.error)

            confirm_label = "确认采用该预览并导出静态结果" if language == "中文" else "Confirm this preview and export static results"
            if preview_result.status == "success" and st.button(confirm_label, type="primary", key=f"{picker_key}-{selected_sheet}-confirm-button", width="stretch"):
                context.results.append(preview_result)
                context.tool_history.append(preview_result)
                if preview_result.summary.get("spectrum_xlsx"):
                    context.spectrum_path = Path(str(preview_result.summary["spectrum_xlsx"]))
                refresh_zip_from_context(context)
                save_current_file_state()
                st.session_state[open_state_key] = False
                st.rerun()

    picker_dialog()


def render_context_outputs(context: AgentRuntimeContext | None, language: str) -> None:
    if context and context.uploaded_path:
        st.info(t(language, "current_file", filename=Path(context.uploaded_path).name))
        active_suffix = Path(context.uploaded_path).suffix.lower()
        st.caption(t(language, "png_upload_hint") if active_suffix == ".png" else t(language, "upload_hint"))

    render_artifact_rail(context, language)
    st.markdown("<div class='t2-section-divider'></div>", unsafe_allow_html=True)

    if context and context.validation:
        st.markdown(t(language, "diagnosis"))
        render_result(context.validation)

    if context and context.repaired_path:
        st.markdown(t(language, "standardized_file"))
        st.success(t(language, "standardized_file_name", filename=Path(context.repaired_path).name))

    if context and context.results:
        st.markdown(t(language, "tool_results"))
        for idx, result in enumerate(context.results):
            render_result(result)
            render_lcurve_parameter_picker(context, result, idx, language)

    if context and context.report:
        st.markdown(t(language, "report"))
        report = context.report
        render_result(report)
        if report.artifacts:
            report_path = Path(report.artifacts[0])
            if report_path.exists():
                render_chat_content(report_path.read_text(encoding="utf-8"), collect_context_artifacts(context))

    if st.session_state.zip_bytes:
        st.caption(t(language, "download_caption"))


def render_trace(trace: list[dict], expanded: bool = False) -> None:
    if not trace:
        return

    language = st.session_state.get("language", "中文")
    with st.expander(t(language, "trace_title"), expanded=expanded):
        st.caption(t(language, "trace_caption"))
        for idx, event in enumerate(trace, start=1):
            kind = event.get("kind", "")
            if kind == "plan":
                st.markdown(f"**{idx}. {t(language, 'trace_plan')}**: {event.get('message', '')}")
            elif kind == "tool_call":
                st.markdown(f"**{idx}. {t(language, 'trace_call')}**: `{event.get('tool_name')}`")
                args = event.get("arguments") or {}
                if args:
                    st.json(args)
            elif kind == "tool_result":
                status = event.get("status")
                tool_name = event.get("tool_name")
                st.markdown(f"**{idx}. {t(language, 'trace_result')}**: `{tool_name}` -> `{status}`")
                st.write(event.get("message", ""))
                if event.get("error"):
                    st.code(event["error"])
                summary_keys = event.get("summary_keys") or []
                if summary_keys:
                    st.caption(t(language, "trace_fields") + ", ".join(summary_keys[:12]))
                artifact_count = event.get("artifact_count", 0)
                if artifact_count:
                    st.caption(t(language, "trace_artifacts", count=artifact_count))


def reset_agent_context(uploaded_path: Path) -> None:
    workspace = make_file_workspace(uploaded_path)
    all_paths = [Path(path) for path in st.session_state.get("uploaded_paths", [str(uploaded_path)])]
    st.session_state.uploaded_path = str(uploaded_path)
    st.session_state.agent_context = AgentRuntimeContext(workspace=workspace, uploaded_path=uploaded_path, uploaded_paths=all_paths)
    st.session_state.agent_messages = []
    st.session_state.display_messages = [
        (
            "assistant",
            t(st.session_state.language, "upload_received"),
        )
    ]
    st.session_state.welcome_language = st.session_state.language
    st.session_state.display_traces = [[]]
    st.session_state.display_artifacts = [[]]
    st.session_state.zip_bytes = None
    path_key = str(uploaded_path)
    st.session_state.file_contexts[path_key] = st.session_state.agent_context
    st.session_state.file_agent_messages[path_key] = st.session_state.agent_messages
    st.session_state.file_display_messages[path_key] = st.session_state.display_messages
    st.session_state.file_display_traces[path_key] = st.session_state.display_traces
    st.session_state.file_display_artifacts[path_key] = st.session_state.display_artifacts
    st.session_state.file_zip_bytes[path_key] = st.session_state.zip_bytes
    st.session_state.file_welcome_language[path_key] = st.session_state.welcome_language
    st.session_state.loaded_active_uploaded_path = path_key


def start_new_task() -> None:
    """Clear UI memory and start a fresh task workspace without deleting old files."""

    st.session_state.workspace = None
    st.session_state.uploaded_path = None
    st.session_state.uploaded_paths = []
    st.session_state.loaded_active_uploaded_path = None
    st.session_state.file_contexts = {}
    st.session_state.file_agent_messages = {}
    st.session_state.file_display_messages = {}
    st.session_state.file_display_traces = {}
    st.session_state.file_display_artifacts = {}
    st.session_state.file_zip_bytes = {}
    st.session_state.file_welcome_language = {}
    st.session_state.agent_context = None
    st.session_state.agent_messages = []
    st.session_state.display_messages = []
    st.session_state.welcome_language = st.session_state.language
    st.session_state.display_traces = []
    st.session_state.display_artifacts = []
    st.session_state.zip_bytes = None


def current_context() -> AgentRuntimeContext | None:
    active_path = st.session_state.get("loaded_active_uploaded_path")
    if active_path and active_path in st.session_state.file_contexts:
        return st.session_state.file_contexts[active_path]
    return st.session_state.agent_context


def refresh_zip_from_context(context: AgentRuntimeContext) -> None:
    st.session_state.zip_bytes = make_zip(collect_context_artifacts(context))
    active_path = st.session_state.get("loaded_active_uploaded_path")
    if active_path:
        st.session_state.file_zip_bytes[active_path] = st.session_state.zip_bytes


def apply_workspace_style() -> None:
    """Apply the agent-workbench shell without changing processing logic."""

    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 0.7rem;
            padding-bottom: 7.5rem;
            max-width: 1320px;
        }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 18% 0%, rgba(37, 99, 235, 0.08), transparent 26rem),
                linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
        }
        h1 {
            letter-spacing: 0 !important;
        }
        div[data-testid="stVerticalBlock"] > div:has(.t2-topbar) {
            margin-bottom: 0.35rem;
        }
        .t2-topbar {
            border: 1px solid rgba(148, 163, 184, 0.32);
            background: rgba(255, 255, 255, 0.86);
            border-radius: 8px;
            padding: 0.32rem 0.62rem;
            box-shadow: 0 6px 14px rgba(15, 23, 42, 0.05);
            line-height: 1.25;
        }
        .t2-kicker {
            color: #2563eb;
            font-size: 0.58rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .t2-title {
            color: #0f172a;
            font-size: clamp(0.98rem, 1.18vw, 1.28rem);
            font-weight: 760;
            margin: 0 0 0.03rem;
        }
        .t2-subtitle {
            color: #475569;
            max-width: 860px;
            font-size: 0.72rem;
            line-height: 1.25;
            margin: 0;
        }
        .t2-page-tools {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            min-height: 0.25rem;
        }
        .t2-chat-toolbar {
            display: flex;
            align-items: flex-end;
            justify-content: space-between;
            gap: 0.75rem;
        }
        .t2-panel-title {
            color: #0f172a;
            font-size: 0.94rem;
            font-weight: 730;
            margin: 0 0 0.35rem;
        }
        .t2-muted {
            color: #64748b;
            font-size: 0.86rem;
        }
        .t2-chat-scroll {
            max-height: calc(100vh - 250px);
            overflow-y: auto;
            padding: 0.35rem 0.55rem 5.6rem 0;
        }
        .t2-artifact-card {
            border: 1px solid rgba(148, 163, 184, 0.28);
            border-radius: 8px;
            background: #ffffff;
            padding: 0.75rem;
            margin: 0.55rem 0;
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
        }
        .t2-artifact-name {
            color: #0f172a;
            font-weight: 680;
            overflow-wrap: anywhere;
        }
        .t2-artifact-meta {
            color: #64748b;
            font-size: 0.78rem;
            margin-top: 0.15rem;
        }
        .t2-right-rail {
            position: sticky;
            top: 1rem;
        }
        .t2-section-divider {
            height: 1px;
            background: rgba(148, 163, 184, 0.32);
            margin: 0.7rem 0;
        }
        div[data-testid="stChatInput"] {
            position: fixed;
            left: max(1.5rem, calc((100vw - 1120px) / 2));
            bottom: 1rem;
            width: min(660px, calc((100vw - 3rem) * 0.62 - 2rem));
            z-index: 1000;
            padding: 0.65rem;
            border: 1px solid rgba(148, 163, 184, 0.35);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.94);
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.18);
            backdrop-filter: blur(10px);
        }
        div[data-testid="stChatInput"] textarea {
            min-height: 3.2rem !important;
        }
        div[data-testid="stVerticalBlock"] > div:has(.t2-floating-model-anchor) + div {
            position: fixed;
            left: calc(max(1.5rem, calc((100vw - 1120px) / 2)) + min(660px, calc((100vw - 3rem) * 0.62 - 2rem)) - 180px);
            bottom: 1.95rem;
            z-index: 1003;
            width: 128px;
        }
        div[data-testid="stVerticalBlock"] > div:has(.t2-floating-model-anchor) + div button {
            min-height: 2.35rem;
            border-radius: 999px;
            border: 0;
            background: transparent;
            box-shadow: none;
            color: #334155;
            font-weight: 650;
            padding-inline: 0.45rem;
        }
        @media (max-width: 900px) {
            .block-container {
                padding-bottom: 8.5rem;
            }
            .t2-chat-scroll {
                max-height: none;
                overflow: visible;
                padding-bottom: 1rem;
            }
            .t2-right-rail {
                position: static;
            }
            div[data-testid="stChatInput"] {
                left: 0.75rem;
                right: 0.75rem;
                width: auto;
                bottom: 0.75rem;
            }
            div[data-testid="stVerticalBlock"] > div:has(.t2-floating-model-anchor) + div {
                left: auto;
                right: 4.6rem;
                bottom: 1.55rem;
                width: 116px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def artifact_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in IMAGE_SUFFIXES:
        return "image"
    if suffix in TABLE_SUFFIXES:
        return "table"
    if suffix in REPORT_SUFFIXES:
        return "report"
    if suffix == ".zip":
        return "zip"
    return "file"


def artifact_kind_label(language: str, kind: str) -> str:
    labels = {
        "中文": {
            "image": "图像",
            "table": "表格",
            "report": "报告",
            "zip": "压缩包",
            "file": "文件",
        },
        "English": {
            "image": "Figure",
            "table": "Table",
            "report": "Report",
            "zip": "Archive",
            "file": "File",
        },
    }
    return labels.get(language, labels["中文"]).get(kind, kind)


def format_file_size(path: Path) -> str:
    try:
        size = path.stat().st_size
    except OSError:
        return ""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


def collect_turn_artifacts(results: list[AgentToolResult]) -> list[str]:
    artifacts: list[str] = []
    seen: set[str] = set()
    for result in results:
        for item in result.artifacts:
            path = Path(item)
            if not path.exists() or not path.is_file():
                continue
            resolved = str(path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            artifacts.append(str(path))
    return artifacts


def render_artifact_chip(path: Path, language: str, key_prefix: str, compact: bool = False) -> None:
    if not path.exists() or not path.is_file():
        return

    kind = artifact_kind(path)
    meta = f"{artifact_kind_label(language, kind)}"
    size = format_file_size(path)
    if size:
        meta = f"{meta} · {size}"

    st.markdown(
        f"""
        <div class="t2-artifact-card">
            <div class="t2-artifact-name">{html.escape(path.name)}</div>
            <div class="t2-artifact-meta">{meta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if kind == "image" and not compact:
        st.image(str(path), caption=path.name, width="stretch")
    try:
        data = path.read_bytes()
    except OSError:
        return
    st.download_button(
        t(language, "download_artifact"),
        data=data,
        file_name=path.name,
        mime="application/octet-stream",
        width="stretch",
        key=f"{key_prefix}-{path.name}-{path.stat().st_mtime_ns}",
    )


def render_turn_artifacts(paths: list[str], language: str, message_index: int) -> None:
    existing = [Path(path) for path in paths if Path(path).exists()]
    if not existing:
        return

    with st.expander(t(language, "turn_artifacts", count=len(existing)), expanded=True):
        for idx, path in enumerate(existing[:6]):
            render_artifact_chip(path, language, f"chat-artifact-{message_index}-{idx}", compact=True)
        if len(existing) > 6:
            st.caption(t(language, "more_artifacts", count=len(existing) - 6))


def render_intro_dialog(language: str) -> None:
    if st.session_state.get("intro_suppressed"):
        return
    if st.session_state.get("intro_seen"):
        return
    st.session_state.intro_seen = True

    @st.dialog(t(language, "intro_title"), width="large")
    def intro() -> None:
        st.markdown(t(language, "intro_body"))
        dont_show = st.checkbox(t(language, "intro_dont_show"))
        if st.button(t(language, "intro_start"), type="primary"):
            if dont_show:
                st.session_state.intro_suppressed = True
                st.query_params[INTRO_QUERY_KEY] = "1"
            st.rerun()

    intro()


def render_topbar(language: str) -> None:
    st.markdown(
        f"""
        <div class="t2-topbar">
            <div class="t2-kicker">{t(language, "workspace_kicker")}</div>
            <div class="t2-title">{t(language, "page_title")}</div>
            <p class="t2-subtitle">{t(language, "caption")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_artifact_rail(context: AgentRuntimeContext | None, language: str) -> None:
    st.markdown(f"<div class='t2-right-rail'><div class='t2-panel-title'>{t(language, 'artifact_rail')}</div>", unsafe_allow_html=True)
    st.caption(t(language, "artifact_rail_caption"))

    if st.session_state.zip_bytes:
        st.download_button(
            t(language, "download_zip"),
            data=st.session_state.zip_bytes,
            file_name="t2_agent_results.zip",
            mime="application/zip",
            width="stretch",
            key="rail-download-zip",
        )

    artifacts = collect_context_artifacts(context) if context else []
    if not artifacts:
        st.info(t(language, "no_artifacts"))
        st.markdown("</div>", unsafe_allow_html=True)
        return

    image_paths = [path for path in artifacts if artifact_kind(path) == "image"]
    table_paths = [path for path in artifacts if artifact_kind(path) == "table"]
    report_paths = [path for path in artifacts if artifact_kind(path) == "report"]
    other_paths = [path for path in artifacts if artifact_kind(path) not in {"image", "table", "report"}]

    if image_paths:
        st.markdown(t(language, "latest_figures"))
        for idx, path in enumerate(image_paths[-4:]):
            render_artifact_chip(path, language, f"rail-image-{idx}")

    with st.expander(t(language, "artifact_files", count=len(artifacts)), expanded=not image_paths):
        for idx, path in enumerate([*report_paths, *table_paths, *other_paths]):
            render_artifact_chip(path, language, f"rail-file-{idx}", compact=True)

    st.markdown("</div>", unsafe_allow_html=True)


def exportable_assistant_analysis(messages: list[tuple[str, str]], language: str) -> list[str]:
    """Return substantive assistant analyses that should be preserved in the final report."""

    seed_messages = set(WELCOME_MESSAGES.values()) | {
        t("中文", "upload_received"),
        t("English", "upload_received"),
        t("中文", "missing_key_reply"),
        t("English", "missing_key_reply"),
    }
    excluded_fragments = (
        "Markdown report generated",
        "Markdown 报告已生成",
        "I called several rounds of tools",
        "我已经调用了多轮工具",
    )
    analyses: list[str] = []
    seen: set[str] = set()
    for role, content in messages:
        text = content.strip()
        if role != "assistant" or not text or text in seed_messages:
            continue
        if any(fragment in text for fragment in excluded_fragments):
            continue
        if len(text) < 35:
            continue
        normalized = re.sub(r"\s+", " ", text)
        if normalized in seen:
            continue
        seen.add(normalized)
        analyses.append(text)
    return analyses[-6:]


def enhance_report_with_conversation(report: AgentToolResult | None, messages: list[tuple[str, str]], language: str) -> bool:
    """Inject useful chat-side analysis into the Markdown report artifact."""

    if report is None or not report.artifacts:
        return False
    report_path = Path(report.artifacts[0])
    if not report_path.exists():
        return False

    analyses = exportable_assistant_analysis(messages, language)
    original = report_path.read_text(encoding="utf-8")
    cleaned = re.sub(
        rf"\n?{re.escape(REPORT_ANALYSIS_START)}.*?{re.escape(REPORT_ANALYSIS_END)}\n?",
        "\n",
        original,
        flags=re.DOTALL,
    ).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    if not analyses:
        if cleaned != original.strip():
            report_path.write_text(cleaned + "\n", encoding="utf-8")
            return True
        return False

    english = language == "English"
    section = [
        REPORT_ANALYSIS_START,
        "## Conversation-Based Analysis" if english else "## 对话综合分析",
        "",
        (
            "The following analysis was preserved from the assistant's conversation-side interpretation, so the exported report reflects the fuller reasoning shown in the chat."
            if english
            else "以下内容来自左侧对话中的分析与总结，用于让导出的最终报告保留更完整的解释过程。"
        ),
        "",
    ]
    for idx, analysis in enumerate(analyses, start=1):
        section.extend([f"### Analysis {idx}" if english else f"### 分析 {idx}", analysis, ""])
    section.append(REPORT_ANALYSIS_END)

    lines = cleaned.splitlines()
    insert_at = 1 if lines and lines[0].startswith("# ") else 0
    enhanced = "\n".join(lines[:insert_at] + ["", *section, ""] + lines[insert_at:]).strip() + "\n"
    enhanced = re.sub(r"\n{3,}", "\n\n", enhanced)
    if enhanced.strip() == original.strip():
        return False
    report_path.write_text(enhanced, encoding="utf-8")
    return True


def run_agent_prompt(prompt: str, api_key: str, model: str, thinking_enabled: bool, live_results_container=None) -> None:
    context = current_context()
    if context is None:
        workspace = ensure_workspace()
        context = AgentRuntimeContext(workspace=workspace, uploaded_paths=[Path(path) for path in st.session_state.get("uploaded_paths", [])])
        st.session_state.agent_context = context

    language = st.session_state.get("language", "中文")
    st.session_state.display_messages.append(("user", prompt))
    st.session_state.display_traces.append([])
    st.session_state.display_artifacts.append([])
    with st.chat_message("user"):
        st.markdown(prompt)

    live_trace_box = st.empty()
    live_trace: list[dict] = []

    def show_live_trace(event: dict) -> None:
        live_trace.append(event)
        with live_trace_box.container():
            render_trace(live_trace, expanded=True)

    def show_live_tool_result(_result: AgentToolResult) -> None:
        refresh_zip_from_context(context)
        save_current_file_state()
        if live_results_container is not None:
            with live_results_container.container():
                st.subheader(t(language, "data_results"))
                render_context_outputs(context, language)

    with st.status(t(language, "running_status"), expanded=True) as status:
        result = run_deepseek_agent_turn(
            api_key=api_key,
            model=model,
            thinking_enabled=thinking_enabled,
            user_message=prompt,
            context=context,
            prior_messages=st.session_state.agent_messages,
            on_trace=show_live_trace,
            on_tool_result=show_live_tool_result,
            response_language=language,
        )
        st.session_state.agent_messages = result.messages
        st.session_state.display_messages.append(("assistant", result.assistant_message))
        st.session_state.display_traces.append(result.trace)
        st.session_state.display_artifacts.append(collect_turn_artifacts(result.tool_results))
        enhance_report_with_conversation(context.report, st.session_state.display_messages, language)
        refresh_zip_from_context(context)
        save_current_file_state()
        for tool_result in result.tool_results:
            st.write(f"{tool_result.status}: {tool_result.message}")
        status.update(label=t(language, "done_status"), state="complete")


def main() -> None:
    page_language = st.session_state.get("language", "中文")
    st.set_page_config(page_title=t(page_language, "page_title"), layout="wide")
    init_state()
    language = st.session_state.get("language", "中文")
    apply_workspace_style()
    render_intro_dialog(language)

    stored_api_key = get_deepseek_api_key(st.secrets)
    user_api_key = ""

    language_cols = st.columns([0.70, 0.14, 0.16], gap="small")
    with language_cols[1]:
        with st.popover(t(language, "api_settings"), use_container_width=True):
            user_api_key = st.text_input(
                "DeepSeek API Key",
                type="password",
                placeholder="sk-...",
                help=t(language, "api_key_help"),
            )
            if user_api_key.strip() or stored_api_key:
                st.success(t(language, "api_key_ready"))
            else:
                st.warning(t(language, "api_key_missing"))
    with language_cols[2]:
        language = st.selectbox(
            t(language, "language"),
            ["中文", "English"],
            index=0 if language == "中文" else 1,
            format_func=lambda option: t(option, "language_option_zh") if option == "中文" else t(option, "language_option_en"),
            key="language",
            label_visibility="collapsed",
        )
        sync_language_seed_messages()

    render_topbar(language)

    with st.expander(t(language, "task_management"), expanded=False):
        st.caption(t(language, "new_task_caption"))
        action_cols = st.columns([0.5, 0.5])
        with action_cols[0]:
            if st.button(t(language, "new_task"), width="stretch"):
                start_new_task()
                st.rerun()
        with action_cols[1]:
            if st.button(t(language, "show_intro"), width="stretch"):
                st.session_state.intro_seen = False
                st.session_state.intro_suppressed = False
                clear_query_param(INTRO_QUERY_KEY)
                st.rerun()

    left, right = st.columns([0.62, 0.38], gap="large")

    with left:
        st.markdown(f"<div class='t2-panel-title'>{t(language, 'agent_chat')}</div>", unsafe_allow_html=True)
        st.caption(t(language, "chat_caption"))
        traces = st.session_state.get("display_traces", [])
        message_artifacts = st.session_state.get("display_artifacts", [])
        context_artifacts = collect_context_artifacts(current_context()) if current_context() else []
        with st.container(height=520, border=False):
            st.markdown("<div class='t2-chat-scroll'>", unsafe_allow_html=True)
            for idx, (role, content) in enumerate(st.session_state.display_messages):
                with st.chat_message(role):
                    render_chat_content(content, context_artifacts)
                    if role == "assistant" and idx < len(message_artifacts):
                        render_turn_artifacts(message_artifacts[idx], language, idx)
                    if role == "assistant" and idx < len(traces):
                        render_trace(traces[idx])
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<span class='t2-floating-model-anchor'></span>", unsafe_allow_html=True)
        selected_model = st.session_state.get("selected_model", DEFAULT_MODEL)
        thinking_state = bool(st.session_state.get("thinking_enabled", DEFAULT_THINKING_ENABLED))
        model_badge = selected_model.replace("deepseek-", "").replace("-flash", " 快").replace("-pro", " 高")
        if thinking_state:
            model_badge = f"{model_badge}"
        with st.popover(model_badge, use_container_width=True):
            model = st.selectbox(
                t(language, "model"),
                AVAILABLE_MODELS,
                index=AVAILABLE_MODELS.index(selected_model) if selected_model in AVAILABLE_MODELS else AVAILABLE_MODELS.index(DEFAULT_MODEL),
                key="selected_model",
            )
            thinking_enabled = st.toggle(t(language, "thinking_mode"), value=DEFAULT_THINKING_ENABLED, key="thinking_enabled")

        api_key = user_api_key.strip() or stored_api_key
        prompt = st.chat_input(t(language, "chat_placeholder"))
        if prompt:
            if not api_key:
                st.session_state.display_messages.append(("user", prompt))
                st.session_state.display_traces.append([])
                st.session_state.display_artifacts.append([])
                st.session_state.display_messages.append(("assistant", t(language, "missing_key_reply")))
                st.session_state.display_traces.append([])
                st.session_state.display_artifacts.append([])
                save_current_file_state()
                st.rerun()
            run_agent_prompt(prompt, api_key, model, thinking_enabled)
            st.rerun()

    with right:
        st.markdown(f"<div class='t2-panel-title'>{t(language, 'data_results')}</div>", unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            t(language, "uploader"),
            type=["xlsx", "xls", "csv", "pea", "txt", "dat", "png"],
            accept_multiple_files=True,
        )
        register_uploaded_files(uploaded_files or [])

        uploaded_paths = st.session_state.get("uploaded_paths", [])
        if uploaded_paths:
            selected_path = st.selectbox(
                t(language, "active_file"),
                uploaded_paths,
                index=max(0, uploaded_paths.index(st.session_state.loaded_active_uploaded_path))
                if st.session_state.loaded_active_uploaded_path in uploaded_paths
                else 0,
                format_func=lambda path: Path(path).name,
            )
            activate_uploaded_path(Path(selected_path))
            st.caption(t(language, "uploaded_count", count=len(uploaded_paths)))

        context = current_context()
        if context and context.uploaded_path:
            st.info(t(language, "current_file", filename=Path(context.uploaded_path).name))
            active_suffix = Path(context.uploaded_path).suffix.lower()
            st.caption(t(language, "png_upload_hint") if active_suffix == ".png" else t(language, "upload_hint"))

        render_artifact_rail(context, language)
        st.markdown("<div class='t2-section-divider'></div>", unsafe_allow_html=True)

        if context and context.validation:
            st.markdown(t(language, "diagnosis"))
            render_result(context.validation)

        if context and context.repaired_path:
            st.markdown(t(language, "standardized_file"))
            st.success(t(language, "standardized_file_name", filename=Path(context.repaired_path).name))

        if context and context.results:
            st.markdown(t(language, "tool_results"))
            for idx, result in enumerate(context.results):
                render_result(result)
                render_lcurve_parameter_picker(context, result, idx, language)

        if context and context.report:
            st.markdown(t(language, "report"))
            report = context.report
            render_result(report)
            if report.artifacts:
                report_path = Path(report.artifacts[0])
                if report_path.exists():
                    render_chat_content(report_path.read_text(encoding="utf-8"), collect_context_artifacts(context))

        if st.session_state.zip_bytes:
            st.caption(t(language, "download_caption"))


if __name__ == "__main__":
    main()
