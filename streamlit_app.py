from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from uuid import uuid4

import streamlit as st

from t2_agent.agent import AgentRuntimeContext, run_deepseek_agent_turn
from t2_agent.deepseek import get_deepseek_api_key
from t2_agent.i18n import t
from t2_agent.models import AgentToolResult


APP_ROOT = Path(__file__).resolve().parent
RUNS_ROOT = APP_ROOT / "runs"
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
MARKDOWN_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


WELCOME_MESSAGES = {
    "中文": """你好，我是 **T2 反演智能体**。我可以帮你把 NMR T2 衰减数据从“表格”处理成可解释的 T2 谱和报告。

我能做的事：

- 检查 Excel 数据格式，识别时间列、信号列、空列、列顺序不符合工具预期等问题
- 自动整理表格为 `time_ms + signal` 标准格式
- 做 T2 反演：默认用 L-curve 自动选择平滑因子，也支持你指定固定平滑因子
- 生成衰减曲线、T2 谱图、L-curve 图
- 对 T2 谱做 Gaussian 分峰，并解释峰位置和面积比例
- 读取已经生成的结果，解释这个结果说明什么，并给出下一步建议

我现在的边界：

- 专注 T2 decay / T2 spectrum 数据处理
- 不做 CT 图像分割、网格生成、Bloch-Torrey 正演模拟
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
- Read generated results and explain what they mean, with suggestions for next steps

Current boundaries:

- Focused on T2 decay / T2 spectrum processing
- Does not perform CT segmentation, mesh generation, or Bloch-Torrey forward simulation
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
        "agent_context": None,
        "agent_messages": [],
        "display_messages": [],
        "display_traces": [],
        "language": "中文",
        "zip_bytes": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if not st.session_state.display_messages:
        st.session_state.display_messages = [("assistant", welcome_message(st.session_state.language))]
        st.session_state.display_traces = [[]]


def ensure_workspace() -> Path:
    if st.session_state.workspace is None:
        workspace = RUNS_ROOT / uuid4().hex
        workspace.mkdir(parents=True, exist_ok=True)
        st.session_state.workspace = str(workspace)
    return Path(st.session_state.workspace)


def save_upload(uploaded_file) -> Path:
    workspace = ensure_workspace()
    upload_dir = workspace / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    output_path = upload_dir / uploaded_file.name
    output_path.write_bytes(uploaded_file.getbuffer())
    return output_path


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

    image_paths = [Path(path) for path in result.artifacts if Path(path).suffix.lower() in IMAGE_SUFFIXES]
    for image_path in image_paths[:6]:
        if image_path.exists():
            st.image(str(image_path), caption=image_path.name, width="stretch")


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
    workspace = ensure_workspace()
    st.session_state.uploaded_path = str(uploaded_path)
    st.session_state.agent_context = AgentRuntimeContext(workspace=workspace, uploaded_path=uploaded_path)
    st.session_state.agent_messages = []
    st.session_state.display_messages = [
        ("assistant", welcome_message(st.session_state.language)),
        (
            "assistant",
            t(st.session_state.language, "upload_received"),
        )
    ]
    st.session_state.display_traces = [[], []]
    st.session_state.zip_bytes = None


def start_new_task() -> None:
    """Clear UI memory and start a fresh task workspace without deleting old files."""

    st.session_state.workspace = None
    st.session_state.uploaded_path = None
    st.session_state.agent_context = None
    st.session_state.agent_messages = []
    st.session_state.display_messages = [("assistant", welcome_message(st.session_state.language))]
    st.session_state.display_traces = [[]]
    st.session_state.zip_bytes = None


def current_context() -> AgentRuntimeContext | None:
    return st.session_state.agent_context


def refresh_zip_from_context(context: AgentRuntimeContext) -> None:
    st.session_state.zip_bytes = make_zip(collect_context_artifacts(context))


def run_agent_prompt(prompt: str, api_key: str, model: str, thinking_enabled: bool) -> None:
    context = current_context()
    if context is None:
        workspace = ensure_workspace()
        context = AgentRuntimeContext(workspace=workspace)
        st.session_state.agent_context = context

    language = st.session_state.get("language", "中文")
    st.session_state.display_messages.append(("user", prompt))
    st.session_state.display_traces.append([])
    with st.chat_message("user"):
        st.markdown(prompt)

    live_trace_box = st.empty()
    live_trace: list[dict] = []

    def show_live_trace(event: dict) -> None:
        live_trace.append(event)
        with live_trace_box.container():
            render_trace(live_trace, expanded=True)

    with st.status(t(language, "running_status"), expanded=True) as status:
        result = run_deepseek_agent_turn(
            api_key=api_key,
            model=model,
            thinking_enabled=thinking_enabled,
            user_message=prompt,
            context=context,
            prior_messages=st.session_state.agent_messages,
            on_trace=show_live_trace,
            response_language=language,
        )
        st.session_state.agent_messages = result.messages
        st.session_state.display_messages.append(("assistant", result.assistant_message))
        st.session_state.display_traces.append(result.trace)
        refresh_zip_from_context(context)
        for tool_result in result.tool_results:
            st.write(f"{tool_result.status}: {tool_result.message}")
        status.update(label=t(language, "done_status"), state="complete")


def main() -> None:
    page_language = st.session_state.get("language", "中文")
    st.set_page_config(page_title=t(page_language, "page_title"), layout="wide")
    init_state()
    language = st.session_state.get("language", "中文")

    st.title(t(language, "page_title"))
    st.caption(t(language, "caption"))
    st.warning(t(language, "session_warning"))
    with st.expander(t(language, "task_management"), expanded=False):
        st.caption(t(language, "new_task_caption"))
        if st.button(t(language, "new_task")):
            start_new_task()
            st.rerun()

    left, right = st.columns([0.42, 0.58], gap="large")

    with left:
        st.subheader(t(language, "agent_chat"))
        language = st.selectbox(
            t(language, "language"),
            ["中文", "English"],
            index=0 if language == "中文" else 1,
            format_func=lambda option: t(option, "language_option_zh") if option == "中文" else t(option, "language_option_en"),
            key="language",
        )
        model = st.selectbox(t(language, "model"), ["deepseek-v4-flash", "deepseek-v4-pro"], index=0)
        thinking_enabled = st.toggle(t(language, "thinking_mode"), value=False)
        user_api_key = st.text_input(
            "DeepSeek API Key",
            type="password",
            placeholder="sk-...",
            help=t(language, "api_key_help"),
        )
        stored_api_key = get_deepseek_api_key(st.secrets)
        api_key = user_api_key.strip() or stored_api_key
        if api_key:
            st.success(t(language, "api_key_ready"))
        else:
            st.warning(t(language, "api_key_missing"))

        st.markdown(t(language, "chat_window"))
        traces = st.session_state.get("display_traces", [])
        context_artifacts = collect_context_artifacts(current_context()) if current_context() else []
        for idx, (role, content) in enumerate(st.session_state.display_messages):
            with st.chat_message(role):
                render_chat_content(content, context_artifacts)
                if role == "assistant" and idx < len(traces):
                    render_trace(traces[idx])

        prompt = st.chat_input(t(language, "chat_placeholder"))
        if prompt:
            if not api_key:
                st.session_state.display_messages.append(("user", prompt))
                st.session_state.display_traces.append([])
                st.session_state.display_messages.append(("assistant", t(language, "missing_key_reply")))
                st.session_state.display_traces.append([])
                st.rerun()
            run_agent_prompt(prompt, api_key, model, thinking_enabled)
            st.rerun()

    with right:
        st.subheader(t(language, "data_results"))
        uploaded_file = st.file_uploader(t(language, "uploader"), type=["xlsx", "xls"])
        if uploaded_file is not None:
            uploaded_path = save_upload(uploaded_file)
            if st.session_state.uploaded_path != str(uploaded_path):
                reset_agent_context(uploaded_path)
                st.rerun()

        context = current_context()
        if context and context.uploaded_path:
            st.info(t(language, "current_file", filename=Path(context.uploaded_path).name))
            st.caption(t(language, "upload_hint"))

        if context and context.validation:
            st.markdown(t(language, "diagnosis"))
            render_result(context.validation)

        if context and context.repaired_path:
            st.markdown(t(language, "standardized_file"))
            st.success(t(language, "standardized_file_name", filename=Path(context.repaired_path).name))

        if context and context.results:
            st.markdown(t(language, "tool_results"))
            for result in context.results:
                render_result(result)

        if context and context.report:
            st.markdown(t(language, "report"))
            report = context.report
            render_result(report)
            if report.artifacts:
                report_path = Path(report.artifacts[0])
                if report_path.exists():
                    render_chat_content(report_path.read_text(encoding="utf-8"), collect_context_artifacts(context))

        if st.session_state.zip_bytes:
            st.download_button(
                t(language, "download_zip"),
                data=st.session_state.zip_bytes,
                file_name="t2_agent_results.zip",
                mime="application/zip",
                width="stretch",
            )
            st.caption(t(language, "download_caption"))


if __name__ == "__main__":
    main()
