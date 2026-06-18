from pathlib import Path
from zipfile import ZipFile
import io

from t2_agent.models import AgentToolResult
from streamlit_app import (
    DEFAULT_MODEL,
    DEFAULT_THINKING_ENABLED,
    enhance_report_with_conversation,
    exportable_assistant_analysis,
    make_zip,
    resolve_artifact_image_reference,
)


def test_default_chat_model_uses_deepseek_pro_thinking_mode():
    assert DEFAULT_MODEL == "deepseek-v4-pro"
    assert DEFAULT_THINKING_ENABLED is True


def test_agent_tool_result_can_carry_simulation_stage_metadata():
    result = AgentToolResult(
        "success",
        "mesh generated",
        artifacts=["mesh.png"],
        summary={"stage": "mesh", "simulation_stages": {"mesh": ["mesh.png"]}},
    )

    assert result.summary["stage"] == "mesh"
    assert result.summary["simulation_stages"]["mesh"] == ["mesh.png"]


def test_resolve_artifact_image_reference_matches_stem_and_basename(tmp_path):
    image_path = tmp_path / "ExperimentalDecay__amplitude__decay_t2.png"
    image_path.write_bytes(b"fake-png")
    lcurve_path = tmp_path / "amplitude__lcurve.png"
    lcurve_path.write_bytes(b"fake-png")

    artifacts = [image_path, lcurve_path]

    assert resolve_artifact_image_reference("decay_t2", artifacts) == image_path
    assert resolve_artifact_image_reference("amplitude__lcurve.png", artifacts) == lcurve_path


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
