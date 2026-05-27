from pathlib import Path

import pandas as pd
import numpy as np

from t2_agent.guidance import build_parameter_guidance, infer_requested_plan
from t2_agent.tools import (
    generate_report,
    inspect_workbook_schema,
    interpret_results,
    repair_workbook,
    run_gaussian_peaks,
    run_lcurve,
    validate_workbook,
)


ROOT = Path(__file__).resolve().parents[1]
SIMULATION = ROOT / "T2process" / "Example data" / "SimulationDecay.xlsx"
SWAPPED_EXPERIMENTAL = ROOT / "T2process" / "Example data" / "ExperimentalDecay.xlsx"


def test_validate_workbook_detects_decay_data_and_recommends_seconds_scale():
    result = validate_workbook(SIMULATION)

    assert result.status == "success"
    assert result.summary["data_kind"] == "decay"
    assert result.summary["signal_column_count"] >= 1
    assert result.summary["recommended_time_to_ms_scale"] == 1000.0
    assert "第 1 列" in result.message


def test_repair_workbook_writes_standardized_time_ms_file(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path, validation.summary["recommended_time_to_ms_scale"])

    assert repaired.status == "success"
    output_path = Path(repaired.artifacts[0])
    assert output_path.exists()

    frame = pd.read_excel(output_path)
    assert list(frame.columns)[:2] == ["time_ms", "Peak"]
    assert frame["time_ms"].max() > 1.0


def test_validate_and_repair_experimental_decay_fixture(tmp_path):
    schema = inspect_workbook_schema(SWAPPED_EXPERIMENTAL)
    assert schema.status == "success"
    labels = [profile["label"] for profile in schema.summary["column_profiles"]]
    assert "Time" in labels
    assert "Peak" in labels

    result = validate_workbook(SWAPPED_EXPERIMENTAL)

    assert result.status == "success"
    assert result.summary["time_column_label"] == "Time"
    assert result.summary["signal_column_labels"] == ["Peak"]
    assert result.summary["column_order_issue"] == "none"
    assert "Time" in result.message
    assert "Peak" in result.message

    repaired = repair_workbook(SWAPPED_EXPERIMENTAL, tmp_path, result.summary["recommended_time_to_ms_scale"])
    frame = pd.read_excel(repaired.artifacts[0])

    assert list(frame.columns)[:2] == ["time_ms", "Peak"]
    assert frame["time_ms"].iloc[0] == 0.1005
    assert frame["Peak"].iloc[0] == 7282.1999


def test_validate_workbook_handles_multi_signal_layout_without_named_headers(tmp_path):
    path = tmp_path / "multi_signal.xlsx"
    pd.DataFrame(
        [
            [0.1, 100.0, 80.0],
            [0.2, 92.0, 70.0],
            [0.3, 85.0, 62.0],
            [0.4, 77.0, 55.0],
        ]
    ).to_excel(path, index=False, header=False)

    result = validate_workbook(path)
    repaired = repair_workbook(path, tmp_path, result.summary["recommended_time_to_ms_scale"])
    frame = pd.read_excel(repaired.artifacts[0])

    assert result.status == "success"
    assert result.summary["time_column_excel_index"] == 1
    assert result.summary["signal_excel_columns"] == [2, 3]
    assert list(frame.columns) == ["time_ms", "col_2", "col_3"]


def test_guidance_explains_regularization_and_defaults_to_lcurve_for_new_user():
    plan = infer_requested_plan("我不懂参数，只想做T2反演")
    guidance = build_parameter_guidance(plan)

    assert plan.workflow == "lcurve_inversion"
    assert plan.needs_gaussian is False
    assert "平滑因子" in guidance
    assert "L-curve" in guidance
    assert "默认" in guidance


def test_guidance_can_render_english_for_english_ui():
    plan = infer_requested_plan("I do not understand the parameters, please choose automatically")
    guidance = build_parameter_guidance(plan, language="English")

    assert "Smoothing/regularization factor" in guidance
    assert "Default recommendation" in guidance
    assert "平滑因子" not in guidance


def test_guidance_extracts_fixed_regularization_and_peak_count():
    plan = infer_requested_plan("我要固定平滑因子 1，然后分两个峰")
    guidance = build_parameter_guidance(plan)

    assert plan.workflow == "fixed_nnls"
    assert plan.regularization == 1.0
    assert plan.needs_gaussian is True
    assert plan.peak_count == 2
    assert "2 个峰" in guidance


def test_lcurve_gaussian_and_report_tools_create_artifacts(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path, validation.summary["recommended_time_to_ms_scale"])
    repaired_workbook = Path(repaired.artifacts[0])

    lcurve = run_lcurve(
        repaired_workbook,
        tmp_path / "lcurve",
        {
            "num_bins": 60,
            "alpha_count": 12,
            "time_to_ms_scale": 1.0,
            "trim_from_peak": True,
        },
    )
    assert lcurve.status == "success"
    assert any(path.endswith("_spectrum.xlsx") for path in lcurve.artifacts)
    assert any(path.endswith("_decay_t2.png") for path in lcurve.artifacts), lcurve.summary.get("paired_plot_warning")

    gaussian = run_gaussian_peaks(
        Path(lcurve.summary["spectrum_xlsx"]),
        tmp_path / "gaussian",
        {"peak_count": 2},
    )
    assert gaussian.status == "success", gaussian.error
    assert gaussian.summary["peak_count"] == 2
    assert any(path.endswith("_summary.csv") for path in gaussian.artifacts)

    report = generate_report(
        tmp_path / "report",
        user_goal="我不懂参数，只想做T2反演并分两个峰",
        validation=validation,
        workflow_results=[lcurve, gaussian],
        parameter_notes=build_parameter_guidance(infer_requested_plan("我不懂参数，只想做T2反演并分两个峰")),
    )
    assert report.status == "success"
    report_text = Path(report.artifacts[0]).read_text(encoding="utf-8")
    assert "T2 反演智能体报告" in report_text
    assert "平滑因子" in report_text


def test_generate_report_can_render_english(tmp_path):
    report = generate_report(
        tmp_path / "report",
        user_goal="Run an English report",
        validation=validate_workbook(SIMULATION, language="English"),
        workflow_results=[],
        parameter_notes=build_parameter_guidance(infer_requested_plan("automatic T2 inversion"), language="English"),
        language="English",
    )

    assert report.status == "success"
    report_text = Path(report.artifacts[0]).read_text(encoding="utf-8")
    assert "T2 Inversion Agent Report" in report_text
    assert "User Goal" in report_text
    assert "T2 反演智能体报告" not in report_text


def test_gaussian_decomposition_does_not_require_removed_numpy_trapz(tmp_path, monkeypatch):
    if hasattr(np, "trapz"):
        monkeypatch.delattr(np, "trapz")

    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path, validation.summary["recommended_time_to_ms_scale"])
    lcurve = run_lcurve(
        Path(repaired.artifacts[0]),
        tmp_path / "lcurve",
        {"num_bins": 60, "alpha_count": 12, "time_to_ms_scale": 1.0},
    )

    gaussian = run_gaussian_peaks(
        Path(lcurve.summary["spectrum_xlsx"]),
        tmp_path / "gaussian",
        {"peak_count": 2},
    )

    assert gaussian.status == "success", gaussian.error
    assert any(path.endswith("_gaussian.png") for path in gaussian.artifacts)


def test_interpret_results_reads_lcurve_outputs_and_explains_main_peak(tmp_path):
    validation = validate_workbook(SIMULATION)
    repaired = repair_workbook(SIMULATION, tmp_path, validation.summary["recommended_time_to_ms_scale"])
    lcurve = run_lcurve(
        Path(repaired.artifacts[0]),
        tmp_path / "lcurve",
        {"num_bins": 60, "alpha_count": 12, "time_to_ms_scale": 1.0},
    )

    interpretation = interpret_results([lcurve], tmp_path / "interpretation")

    assert interpretation.status == "success"
    assert "最佳平滑因子" in interpretation.message
    assert "主峰" in interpretation.message
    assert Path(interpretation.artifacts[0]).exists()
