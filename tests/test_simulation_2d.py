from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from t2_agent.simulation_2d import (
    SOLID,
    WATER,
    inspect_png_phase_map,
    write_standard_decay_workbook,
)


def _write_phase_png(path: Path) -> None:
    rgb = np.full((10, 12, 3), 255, dtype=np.uint8)
    rgb[2:8, 2:10] = [255, 255, 0]
    rgb[3:7, 4:8] = [255, 0, 0]
    Image.fromarray(rgb, mode="RGB").save(path)


def test_inspect_png_phase_map_crops_white_border_and_counts_phases(tmp_path: Path):
    png_path = tmp_path / "phase.png"
    _write_phase_png(png_path)

    result = inspect_png_phase_map(png_path, tmp_path / "inspect")

    assert result.status == "success"
    assert result.raw_shape == [10, 12]
    assert result.cropped_shape == [6, 8]
    assert result.phase_counts["water_px"] == 16
    assert result.phase_counts["solid_px"] == 32
    assert result.phase_counts["outside_px"] == 0
    assert result.cropped_png.exists()
    assert result.preview_png.exists()
    assert result.labels.shape == (6, 8)
    assert np.count_nonzero(result.labels == WATER) == 16
    assert np.count_nonzero(result.labels == SOLID) == 32


def test_inspect_png_phase_map_rejects_missing_water(tmp_path: Path):
    png_path = tmp_path / "solid.png"
    rgb = np.full((5, 5, 3), [255, 255, 0], dtype=np.uint8)
    Image.fromarray(rgb, mode="RGB").save(png_path)

    result = inspect_png_phase_map(png_path, tmp_path / "inspect")

    assert result.status == "failed"
    assert result.error == "no_liquid_pixels"


def test_write_standard_decay_workbook_uses_time_ms_signal_columns(tmp_path: Path):
    output = write_standard_decay_workbook(
        tmp_path / "decay.xlsx",
        time_ms=np.array([0.0, 5.0, 10.0]),
        signal=np.array([1.0, 0.8, 0.6]),
    )

    frame = pd.read_excel(output)

    assert list(frame.columns) == ["time_ms", "signal"]
    assert frame["time_ms"].tolist() == [0, 5, 10]
    assert frame["signal"].tolist() == [1.0, 0.8, 0.6]
