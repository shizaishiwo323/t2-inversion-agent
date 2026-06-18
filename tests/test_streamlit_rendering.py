from pathlib import Path
from zipfile import ZipFile
import io

import pandas as pd

from t2_agent.agent import AgentRuntimeContext
from t2_agent.models import AgentToolResult
import streamlit_app
from streamlit_app import (
    DEFAULT_MODEL,
    DEFAULT_THINKING_ENABLED,
    INTRO_QUERY_KEY,
    artifact_kind,
    collect_turn_artifacts,
    clear_query_param,
    enhance_report_with_conversation,
    exportable_assistant_analysis,
    make_zip,
    query_param_enabled,
    resolve_artifact_image_reference,
    selected_alpha_fixed_nnls_params,
    should_offer_lcurve_parameter_picker,
    lcurve_picker_state_keys,
)


def test_default_chat_model_uses_deepseek_pro_thinking_mode():
    assert DEFAULT_MODEL == "deepseek-v4-pro"
    assert DEFAULT_THINKING_ENABLED is True


def test_resolve_artifact_image_reference_matches_stem_and_basename(tmp_path):
    image_path = tmp_path / "ExperimentalDecay__amplitude__decay_t2.png"
    image_path.write_bytes(b"fake-png")
    lcurve_path = tmp_path / "amplitude__lcurve.png"
    lcurve_path.write_bytes(b"fake-png")

    artifacts = [image_path, lcurve_path]

    assert resolve_artifact_image_reference("decay_t2", artifacts) == image_path
    assert resolve_artifact_image_reference("amplitude__lcurve.png", artifacts) == lcurve_path


def test_artifact_kind_groups_figures_tables_and_reports():
    assert artifact_kind(Path("plot.png")) == "image"
    assert artifact_kind(Path("spectrum.xlsx")) == "table"
    assert artifact_kind(Path("summary.csv")) == "table"
    assert artifact_kind(Path("report.md")) == "report"
    assert artifact_kind(Path("notes.bin")) == "file"


def test_collect_turn_artifacts_keeps_existing_unique_files(tmp_path):
    figure = tmp_path / "decay_t2.png"
    table = tmp_path / "summary.xlsx"
    missing = tmp_path / "missing.csv"
    figure.write_bytes(b"figure")
    table.write_bytes(b"table")

    artifacts = collect_turn_artifacts(
        [
            AgentToolResult("success", "first", artifacts=[str(figure), str(table)]),
            AgentToolResult("success", "duplicate", artifacts=[str(figure), str(missing)]),
        ]
    )

    assert artifacts == [str(figure), str(table)]


def test_intro_query_preference_helpers(monkeypatch):
    query_params = {INTRO_QUERY_KEY: "1", "other": "kept"}
    monkeypatch.setattr(streamlit_app.st, "query_params", query_params)

    assert query_param_enabled(INTRO_QUERY_KEY) is True

    clear_query_param(INTRO_QUERY_KEY)

    assert INTRO_QUERY_KEY not in query_params
    assert query_params["other"] == "kept"


def test_resolve_artifact_image_reference_rejects_non_images(tmp_path):
    table_path = tmp_path / "summary.csv"
    table_path.write_text("x,y\n1,2\n")

    assert resolve_artifact_image_reference("summary.csv", [table_path]) is None


def test_make_zip_preserves_batch_result_folders(tmp_path):
    file_a_report = tmp_path / "batch_results" / "sample_a.xlsx" / "report" / "report.md"
    file_b_report = tmp_path / "batch_results" / "sample_b.xlsx" / "report" / "report.md"
    file_a_report.parent.mkdir(parents=True)
    file_b_report.parent.mkdir(parents=True)
    file_a_report.write_text("a", encoding="utf-8")
    file_b_report.write_text("b", encoding="utf-8")

    zip_bytes = make_zip([file_a_report, file_b_report])

    with ZipFile(io.BytesIO(zip_bytes)) as archive:
        names = set(archive.namelist())

    assert "batch_results/sample_a.xlsx/report/report.md" in names
    assert "batch_results/sample_b.xlsx/report/report.md" in names


def test_make_zip_preserves_gaussian_peak_count_folders(tmp_path):
    peak_2 = tmp_path / "tasks" / "sample.xlsx" / "gaussian" / "peaks_2" / "sample__gaussian_figures" / "col_2__gaussian.png"
    peak_3 = tmp_path / "tasks" / "sample.xlsx" / "gaussian" / "peaks_3" / "sample__gaussian_figures" / "col_2__gaussian.png"
    peak_2.parent.mkdir(parents=True)
    peak_3.parent.mkdir(parents=True)
    peak_2.write_bytes(b"two")
    peak_3.write_bytes(b"three")

    zip_bytes = make_zip([peak_2, peak_3])

    with ZipFile(io.BytesIO(zip_bytes)) as archive:
        names = set(archive.namelist())

    assert "sample.xlsx/gaussian/peaks_2/sample__gaussian_figures/col_2__gaussian.png" in names
    assert "sample.xlsx/gaussian/peaks_3/sample__gaussian_figures/col_2__gaussian.png" in names


def test_make_zip_preserves_parameter_run_folders(tmp_path):
    run_a = tmp_path / "tasks" / "sample.xlsx" / "lcurve" / "bins_50__alpha_n_8" / "sample__lcurve_spectrum.xlsx"
    run_b = tmp_path / "tasks" / "sample.xlsx" / "lcurve" / "bins_80__alpha_n_10" / "sample__lcurve_spectrum.xlsx"
    run_a.parent.mkdir(parents=True)
    run_b.parent.mkdir(parents=True)
    run_a.write_bytes(b"a")
    run_b.write_bytes(b"b")

    zip_bytes = make_zip([run_a, run_b])

    with ZipFile(io.BytesIO(zip_bytes)) as archive:
        names = set(archive.namelist())

    assert "sample.xlsx/lcurve/bins_50__alpha_n_8/sample__lcurve_spectrum.xlsx" in names
    assert "sample.xlsx/lcurve/bins_80__alpha_n_10/sample__lcurve_spectrum.xlsx" in names


def test_should_offer_lcurve_parameter_picker_only_for_successful_lcurve_metrics(tmp_path):
    metrics_path = tmp_path / "sample__lcurve_metrics.xlsx"
    metrics_path.write_bytes(b"fake")
    lcurve_result = AgentToolResult(
        "success",
        "ok",
        summary={"metrics_xlsx": str(metrics_path)},
    )
    failed_result = AgentToolResult(
        "failed",
        "no",
        summary={"metrics_xlsx": str(metrics_path)},
    )
    missing_metrics = AgentToolResult("success", "ok", summary={"metrics_xlsx": str(tmp_path / "missing.xlsx")})

    assert should_offer_lcurve_parameter_picker(lcurve_result) is True
    assert should_offer_lcurve_parameter_picker(failed_result) is False
    assert should_offer_lcurve_parameter_picker(missing_metrics) is False


def test_selected_alpha_fixed_nnls_params_preserve_lcurve_settings():
    lcurve_result = AgentToolResult(
        "success",
        "ok",
        summary={
            "parameters": {
                "num_bins": 240,
                "t2_min_ms": 0.02,
                "t2_max_ms": 50000.0,
                "time_to_ms_scale": 1000.0,
                "trim_from_peak": False,
                "alpha_min": 0.001,
                "alpha_max": 10000.0,
                "alpha_count": 300,
            }
        },
    )

    params = selected_alpha_fixed_nnls_params(lcurve_result, 0.1234)

    assert params == {
        "regularization": 0.1234,
        "num_bins": 240,
        "t2_min_ms": 0.02,
        "t2_max_ms": 50000.0,
        "time_to_ms_scale": 1000.0,
        "trim_from_peak": False,
    }


def test_lcurve_picker_open_state_does_not_reuse_button_widget_key():
    keys = lcurve_picker_state_keys(0)

    assert keys["open_state"] != keys["open_button"]
    assert keys["open_state"].endswith("-state")
    assert keys["open_button"].endswith("-button")


def test_lcurve_picker_render_does_not_mutate_widget_keys(monkeypatch, tmp_path):
    metrics_path = tmp_path / "metrics.xlsx"
    pd.DataFrame(
            {
                "alpha_regularization": [0.001, 0.01, 0.1],
                "residual_norm": [3.0, 2.0, 1.0],
                "roughness_norm": [1.0, 2.0, 3.0],
                "slope_reciprocal": [0.2, 0.3, 0.4],
                "is_selected": [False, True, False],
            }
    ).to_excel(metrics_path, index=False)
    repaired_path = tmp_path / "repaired.xlsx"
    repaired_path.write_bytes(b"placeholder")
    context = AgentRuntimeContext(workspace=tmp_path, repaired_path=repaired_path)
    result = AgentToolResult("success", "ok", summary={"metrics_xlsx": str(metrics_path)})

    class GuardedSessionState(dict):
        def __init__(self):
            super().__init__()
            self.widget_keys: set[str] = set()

        def __setitem__(self, key, value):
            if key in self.widget_keys:
                raise AssertionError(f"attempted to mutate widget key {key}")
            super().__setitem__(key, value)

    class FakeColumn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeStreamlit:
        def __init__(self):
            self.session_state = GuardedSessionState()

        def caption(self, *_args, **_kwargs):
            return None

        def button(self, _label, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return bool(key and (key.endswith("-open-button") or key.endswith("-open")))

        def dialog(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

        def selectbox(self, _label, options, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return list(options)[0]

        def number_input(self, _label, value=None, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return value

        def columns(self, *_args, **_kwargs):
            return [FakeColumn(), FakeColumn()]

        def plotly_chart(self, *_args, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return None

        def success(self, *_args, **_kwargs):
            return None

    fake_st = FakeStreamlit()
    monkeypatch.setattr(streamlit_app, "st", fake_st)

    streamlit_app.render_lcurve_parameter_picker(context, result, 0, "中文")

    keys = lcurve_picker_state_keys(0)
    assert fake_st.session_state[keys["open_state"]] is True
    assert fake_st.session_state["lcurve-alpha-picker-0-Sheet1-alpha"] == 0.01


def test_lcurve_picker_preview_does_not_append_formal_result(monkeypatch, tmp_path):
    metrics_path = tmp_path / "metrics.xlsx"
    pd.DataFrame(
        {
            "alpha_regularization": [0.001, 0.01, 0.1],
            "residual_norm": [3.0, 2.0, 1.0],
            "roughness_norm": [1.0, 2.0, 3.0],
            "slope_reciprocal": [0.2, 0.3, 0.4],
            "is_selected": [False, True, False],
        }
    ).to_excel(metrics_path, index=False)
    repaired_path = tmp_path / "repaired.xlsx"
    repaired_path.write_bytes(b"placeholder")
    context = AgentRuntimeContext(workspace=tmp_path, repaired_path=repaired_path)
    result = AgentToolResult("success", "ok", summary={"metrics_xlsx": str(metrics_path)})
    captured_params: list[dict] = []

    def fake_run_fixed_nnls(_input_workbook, _output_dir, params, language="中文"):
        captured_params.append(dict(params))
        spectrum_path = tmp_path / "preview_spectrum.xlsx"
        pd.DataFrame({"t2_ms": [1.0, 10.0, 100.0], "amplitude": [0.0, 5.0, 0.0]}).to_excel(spectrum_path, index=False)
        return AgentToolResult("success", "preview", artifacts=[str(spectrum_path)], summary={"spectrum_xlsx": str(spectrum_path)})

    class GuardedSessionState(dict):
        def __init__(self):
            super().__init__()
            self.widget_keys: set[str] = set()

        def __setitem__(self, key, value):
            if key in self.widget_keys:
                raise AssertionError(f"attempted to mutate widget key {key}")
            super().__setitem__(key, value)

    class FakeColumn:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class FakeStatus:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def update(self, **_kwargs):
            return None

    class FakeStreamlit:
        def __init__(self):
            self.session_state = GuardedSessionState()

        def caption(self, *_args, **_kwargs):
            return None

        def markdown(self, *_args, **_kwargs):
            return None

        def button(self, _label, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return bool(key and (key.endswith("-open-button") or key.endswith("-preview-button")))

        def dialog(self, *_args, **_kwargs):
            def decorator(fn):
                return fn

            return decorator

        def selectbox(self, _label, options, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return list(options)[0]

        def number_input(self, _label, value=None, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return 0.25

        def columns(self, *_args, **_kwargs):
            return [FakeColumn(), FakeColumn()]

        def plotly_chart(self, *_args, key=None, **_kwargs):
            if key:
                self.session_state.widget_keys.add(key)
            return None

        def success(self, *_args, **_kwargs):
            return None

        def info(self, *_args, **_kwargs):
            return None

        def status(self, *_args, **_kwargs):
            return FakeStatus()

    fake_st = FakeStreamlit()
    monkeypatch.setattr(streamlit_app, "st", fake_st)
    monkeypatch.setattr(streamlit_app, "run_fixed_nnls", fake_run_fixed_nnls)

    streamlit_app.render_lcurve_parameter_picker(context, result, 0, "中文")

    keys = lcurve_picker_state_keys(0)
    assert fake_st.session_state[keys["open_state"]] is True
    assert captured_params[0]["regularization"] == 0.25
    assert context.results == []
    assert context.tool_history == []
    assert "lcurve-alpha-picker-0-Sheet1-preview-result" in fake_st.session_state


def test_enhance_report_with_conversation_exports_substantive_chat_analysis(tmp_path):
    report_path = tmp_path / "report.md"
    report_path.write_text("# T2 反演智能体报告\n\n## 工具运行结果\n- 原始工具摘要\n", encoding="utf-8")
    report = AgentToolResult("success", "ok", artifacts=[str(report_path)])
    messages = [
        ("assistant", "准备好后再上传 Excel，并告诉我你的目标。"),
        (
            "assistant",
            "## 五种分峰方案对比分析\n\n3 峰方案最推荐，因为它在拟合曲线、面积分布和解释稳定性之间取得较好平衡。2 峰偏粗，5 和 6 峰出现过度拆分风险。",
        ),
    ]

    assert enhance_report_with_conversation(report, messages, "中文") is True
    first_text = report_path.read_text(encoding="utf-8")
    assert "## 对话综合分析" in first_text
    assert "五种分峰方案对比分析" in first_text
    assert "3 峰方案最推荐" in first_text

    assert enhance_report_with_conversation(report, messages, "中文") is False
    second_text = report_path.read_text(encoding="utf-8")
    assert second_text.count("## 对话综合分析") == 1
    assert second_text == first_text


def test_exportable_assistant_analysis_filters_seed_messages():
    messages = [
        ("assistant", "准备好后再上传 Excel，并告诉我你的目标。"),
        ("user", "请分析"),
        ("assistant", "太短"),
        ("assistant", "这是一段足够长的分析内容，用于说明不同参数结果的优劣、风险和建议选择，应该进入最终报告导出。"),
    ]

    analyses = exportable_assistant_analysis(messages, "中文")

    assert analyses == ["这是一段足够长的分析内容，用于说明不同参数结果的优劣、风险和建议选择，应该进入最终报告导出。"]
