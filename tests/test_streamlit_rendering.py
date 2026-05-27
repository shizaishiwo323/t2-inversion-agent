from pathlib import Path
from zipfile import ZipFile
import io

from streamlit_app import make_zip, resolve_artifact_image_reference


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
