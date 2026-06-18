# 2D NMR Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first-version 2D NMR simulation workflow that supports rule geometry and red/yellow/white PNG input, uses pyGIMLi triangular meshing, solves a T2 decay curve, sends that decay into the existing T2 inversion pipeline, and shows intermediate artifacts stage by stage in Streamlit.

**Architecture:** Add a focused `t2_agent.simulation_2d` backend that adapts the stable 2D PNG logic from the referenced `For-Bin` repository into importable functions. Expose it through whitelisted tools in `t2_agent.tools`, wire those tools into the DeepSeek function-calling loop, and extend Streamlit rendering so simulation stages appear as they are produced.

**Tech Stack:** Python, Streamlit, pandas, numpy, scipy, matplotlib, Pillow, scikit-image, pyGIMLi, existing `T2process/nmr_t2` pipelines, pytest.

---

## File Structure

- Create: `t2_agent/simulation_2d.py`
  - Owns 2D phase-map validation, white-border cropping, phase preview export, rule-geometry rasterization, pyGIMLi triangular mesh/decay solve, decay export, and simulation summary JSON.

- Modify: `t2_agent/models.py`
  - Adds optional staged-result metadata to `AgentToolResult` without breaking existing callers.
  - Extends `UserWorkflowPlan.workflow` with simulation intents.

- Modify: `t2_agent/guidance.py`
  - Infers simulation requests separately from standalone inversion requests.
  - Adds beginner-facing parameter guidance for 2D simulation.

- Modify: `t2_agent/tools.py`
  - Adds `inspect_2d_geometry_input`, `run_2d_mesh_and_decay`, and `run_2d_simulation_full_workflow`.
  - Converts simulation decay output to a standard `time_ms + signal` workbook and reuses existing `run_lcurve`, `run_fixed_nnls`, `run_gaussian_peaks`, `interpret_results`, and `generate_report`.

- Modify: `t2_agent/agent.py`
  - Adds tool schemas and execution branches for the new simulation tools.
  - Updates the system prompt from T2-only to 2D NMR simulation plus T2 inversion.
  - Tracks `simulation_decay_path` in `AgentRuntimeContext`.

- Modify: `streamlit_app.py`
  - Accepts PNG uploads.
  - Updates welcome copy and upload hints.
  - Groups simulation artifacts by stage in the right results column.

- Modify: `t2_agent/i18n.py`
  - Adds Chinese/English copy for PNG upload, simulation stages, and simulation capability.

- Modify: `requirements.txt`
  - Adds `Pillow`, `scikit-image`, and `pygimli`.

- Create: `tests/test_simulation_2d.py`
  - Tests PNG inspection, white-border cropping, standard decay workbook export, pyGIMLi-gated mesh/decay smoke behavior, and rule geometry validation.

- Modify: `tests/test_agent_tool_loop.py`
  - Tests new tool schemas and fake-client simulation tool execution.

- Modify: `tests/test_streamlit_rendering.py`
  - Tests staged simulation artifact grouping and zip path preservation.

- Modify: `README.md`
  - Documents the new first-version 2D NMR simulation workflow and PNG color convention.

---

### Task 1: Add Dependencies And Shared Result Metadata

**Files:**
- Modify: `requirements.txt`
- Modify: `t2_agent/models.py`
- Test: `tests/test_streamlit_rendering.py`

- [ ] **Step 1: Write the staged-result metadata test**

Add this test to `tests/test_streamlit_rendering.py`:

```python
def test_agent_tool_result_can_carry_simulation_stage_metadata():
    result = AgentToolResult(
        "success",
        "mesh generated",
        artifacts=["mesh.png"],
        summary={"stage": "mesh", "simulation_stages": {"mesh": ["mesh.png"]}},
    )

    assert result.summary["stage"] == "mesh"
    assert result.summary["simulation_stages"]["mesh"] == ["mesh.png"]
```

- [ ] **Step 2: Run the focused test**

Run:

```powershell
pytest tests/test_streamlit_rendering.py::test_agent_tool_result_can_carry_simulation_stage_metadata -q
```

Expected: PASS, because `AgentToolResult.summary` already supports this shape.

- [ ] **Step 3: Extend workflow intent literals**

In `t2_agent/models.py`, replace the `workflow` literal in `UserWorkflowPlan` with:

```python
workflow: Literal[
    "lcurve_inversion",
    "fixed_nnls",
    "gaussian_only",
    "full_analysis",
    "simulation_2d_png",
    "simulation_2d_rule",
    "simulation_2d_full",
] = "lcurve_inversion"
```

- [ ] **Step 4: Add dependencies**

Append these exact lines to `requirements.txt`:

```text
Pillow>=10.0
scikit-image>=0.22
pygimli>=1.5
```

- [ ] **Step 5: Run focused checks**

Run:

```powershell
pytest tests/test_streamlit_rendering.py::test_agent_tool_result_can_carry_simulation_stage_metadata -q
pytest tests/test_t2_agent.py::test_guidance_explains_regularization_and_defaults_to_lcurve_for_new_user -q
```

Expected: both PASS.

- [ ] **Step 6: Commit**

Run:

```powershell
git add requirements.txt t2_agent/models.py tests/test_streamlit_rendering.py
git commit -m "feat: prepare simulation workflow metadata"
```

---

### Task 2: Add PNG Inspection And Decay Workbook Export Backend

**Files:**
- Create: `t2_agent/simulation_2d.py`
- Create: `tests/test_simulation_2d.py`

- [ ] **Step 1: Write PNG inspection tests**

Create `tests/test_simulation_2d.py` with:

```python
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_simulation_2d.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 't2_agent.simulation_2d'`.

- [ ] **Step 3: Implement PNG inspection and workbook export**

Create `t2_agent/simulation_2d.py` with this starting implementation:

```python
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg", force=True)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage


OUTSIDE = np.uint8(0)
WATER = np.uint8(1)
SOLID = np.uint8(2)


@dataclass(frozen=True)
class Simulation2DParams:
    pixel_size_x_um: float = 1.0
    pixel_size_y_um: float = 1.0
    diffusion_um2_per_ms: float = 2.0
    bulk_t2_ms: float = 3000.0
    rho_solid_um_per_ms: float = 0.005
    rho_gas_um_per_ms: float = 0.0
    dt_ms: float = 5.0
    t_max_ms: float = 1500.0
    max_grid_size: int | None = 500
    solver: str = "triangular"
    mesh_bulk_size_um: float = 8.0
    mesh_boundary_size_um: float = 2.0
    mesh_max_points: int = 25000


@dataclass
class PngInspection:
    status: str
    message: str
    input_path: Path
    raw_shape: list[int]
    cropped_shape: list[int]
    phase_counts: dict[str, int]
    labels: np.ndarray
    cropped_png: Path
    preview_png: Path
    error: str | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "input_path": str(self.input_path),
            "raw_shape": self.raw_shape,
            "cropped_shape": self.cropped_shape,
            "phase_counts": self.phase_counts,
            "cropped_png": str(self.cropped_png),
            "preview_png": str(self.preview_png),
            "error": self.error,
        }


def classify_png(rgb: np.ndarray) -> np.ndarray:
    colors = np.asarray(
        [
            [255, 255, 255],
            [255, 0, 0],
            [255, 255, 0],
        ],
        dtype=np.int32,
    )
    labels = np.asarray([OUTSIDE, WATER, SOLID], dtype=np.uint8)
    rgb32 = rgb.astype(np.int32)
    dist2 = np.sum((rgb32[..., None, :] - colors[None, None, :, :]) ** 2, axis=-1)
    return labels[np.argmin(dist2, axis=-1)]


def sample_bbox(labels: np.ndarray) -> tuple[int, int, int, int]:
    sample = labels != OUTSIDE
    if not np.any(sample):
        raise ValueError("No red/yellow sample pixels were found in the PNG.")
    rows, cols = np.where(sample)
    return int(rows.min()), int(rows.max()), int(cols.min()), int(cols.max())


def save_phase_preview(labels: np.ndarray, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rgb = np.zeros((*labels.shape, 3), dtype=np.uint8)
    rgb[labels == OUTSIDE] = [255, 255, 255]
    rgb[labels == WATER] = [255, 0, 0]
    rgb[labels == SOLID] = [255, 255, 0]
    Image.fromarray(rgb, mode="RGB").save(output_path)


def inspect_png_phase_map(png_path: Path, output_dir: Path) -> PngInspection:
    input_path = Path(png_path)
    output_dir = Path(output_dir)
    cropped_png = output_dir / f"{input_path.stem}__cropped_phase.png"
    preview_png = output_dir / f"{input_path.stem}__classified_preview.png"
    try:
        rgb = np.asarray(Image.open(input_path).convert("RGB"))
        labels_full = classify_png(rgb)
        raw_shape = [int(labels_full.shape[0]), int(labels_full.shape[1])]
        row_min, row_max, col_min, col_max = sample_bbox(labels_full)
        labels = labels_full[row_min : row_max + 1, col_min : col_max + 1]
        counts = {
            "outside_px": int(np.sum(labels == OUTSIDE)),
            "water_px": int(np.sum(labels == WATER)),
            "solid_px": int(np.sum(labels == SOLID)),
        }
        save_phase_preview(labels, cropped_png)
        save_phase_preview(labels, preview_png)
        if counts["water_px"] <= 0:
            return PngInspection(
                "failed",
                "PNG phase map has no red liquid/water pixels.",
                input_path,
                raw_shape,
                [int(labels.shape[0]), int(labels.shape[1])],
                counts,
                labels,
                cropped_png,
                preview_png,
                "no_liquid_pixels",
            )
        if counts["solid_px"] <= 0:
            return PngInspection(
                "failed",
                "PNG phase map has no yellow solid pixels.",
                input_path,
                raw_shape,
                [int(labels.shape[0]), int(labels.shape[1])],
                counts,
                labels,
                cropped_png,
                preview_png,
                "no_solid_pixels",
            )
        return PngInspection(
            "success",
            "PNG phase map inspected and white border cropped.",
            input_path,
            raw_shape,
            [int(labels.shape[0]), int(labels.shape[1])],
            counts,
            labels,
            cropped_png,
            preview_png,
        )
    except ValueError as exc:
        return PngInspection("failed", str(exc), input_path, [], [], {}, np.zeros((0, 0), dtype=np.uint8), cropped_png, preview_png, "empty_sample")
    except Exception as exc:
        return PngInspection("failed", "PNG phase-map inspection failed.", input_path, [], [], {}, np.zeros((0, 0), dtype=np.uint8), cropped_png, preview_png, str(exc))


def downsample_nearest(labels: np.ndarray, max_grid_size: int | None) -> tuple[np.ndarray, float]:
    if max_grid_size is None:
        return labels, 1.0
    scale = max(labels.shape) / float(max_grid_size)
    if scale <= 1.0:
        return labels, 1.0
    zoom = 1.0 / scale
    small = ndimage.zoom(labels, zoom=zoom, order=0)
    return small.astype(np.uint8), scale


def write_standard_decay_workbook(path: Path, time_ms: np.ndarray, signal: np.ndarray) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame({"time_ms": np.asarray(time_ms, dtype=float), "signal": np.asarray(signal, dtype=float)})
    frame.to_excel(output_path, index=False)
    return output_path


def write_json_summary(path: Path, payload: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return output_path
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
pytest tests/test_simulation_2d.py -q
```

Expected: all tests in the new file PASS.

- [ ] **Step 5: Commit**

Run:

```powershell
git add t2_agent/simulation_2d.py tests/test_simulation_2d.py
git commit -m "feat: inspect 2d png phase maps"
```

---

### Task 3: Port pyGIMLi Triangular Mesh And Decay Solve

**Files:**
- Modify: `t2_agent/simulation_2d.py`
- Modify: `tests/test_simulation_2d.py`

- [ ] **Step 1: Write pyGIMLi-gated mesh/decay tests**

Append to `tests/test_simulation_2d.py`:

```python
from t2_agent.simulation_2d import Simulation2DParams, run_png_mesh_decay


def pygimli_available() -> bool:
    try:
        import pygimli  # noqa: F401
        import pygimli.meshtools  # noqa: F401
    except Exception:
        return False
    return True


@pytest.mark.skipif(not pygimli_available(), reason="pyGIMLi is not installed")
def test_run_png_mesh_decay_writes_mesh_decay_and_workbook(tmp_path: Path):
    png_path = tmp_path / "phase.png"
    _write_phase_png(png_path)
    params = Simulation2DParams(
        dt_ms=25.0,
        t_max_ms=50.0,
        max_grid_size=None,
        mesh_bulk_size_um=3.0,
        mesh_boundary_size_um=1.5,
        mesh_max_points=5000,
    )

    result = run_png_mesh_decay(png_path, tmp_path / "run", params)

    assert result["status"] == "success"
    assert Path(result["mesh_png"]).exists()
    assert Path(result["pygimli_mesh_bms"]).exists()
    assert Path(result["mesh_quality_csv"]).exists()
    assert Path(result["mesh_quality_histogram_png"]).exists()
    assert Path(result["curve_csv"]).exists()
    assert Path(result["curve_png"]).exists()
    assert Path(result["standard_decay_xlsx"]).exists()
    assert result["time_point_count"] == 3
```

- [ ] **Step 2: Run the new test to verify failure**

Run:

```powershell
pytest tests/test_simulation_2d.py::test_run_png_mesh_decay_writes_mesh_decay_and_workbook -q
```

Expected when pyGIMLi is installed: FAIL with missing `run_png_mesh_decay`. Expected when pyGIMLi is missing: SKIPPED.

- [ ] **Step 3: Port numerical helper functions**

Open the referenced repository file:

```text
C:\Users\imgw\.codex\tmp\nmr-sim-for-bin-9555\advanced_tools\png_phase_nmr_decay.py
```

Copy these function bodies into `t2_agent/simulation_2d.py`, preserving their numerical formulas and adapting imports to the current file:

```text
boundary_kind_for_outside_neighbor
build_water_operator
sample_label_at_xy
xy_to_row_col
contour_to_xy
resample_polyline
unique_points
clean_ordered_polygon
signed_polygon_area
orient_polygon
choose_region_marker
pg_mesh_to_arrays
build_triangular_water_mesh
classify_boundary_edge
assemble_triangular_operator
save_triangular_mesh_plot
triangle_quality_table
mesh_boundary_edge_count
summarize_mesh_quality
save_mesh_quality_histogram
save_pygimli_mesh
solve_decay_triangular
solve_decay_pixel
save_decay_plot
```

At the top of `t2_agent/simulation_2d.py`, add the required imports:

```python
from matplotlib.path import Path as MplPath
import matplotlib.tri as mtri
from scipy.sparse import csr_matrix, diags, eye
from scipy.sparse.linalg import factorized
from skimage import measure

try:
    import pygimli as pg
    import pygimli.meshtools as mt
except Exception:
    pg = None
    mt = None
```

- [ ] **Step 4: Add the importable run wrapper**

Append this function to `t2_agent/simulation_2d.py`:

```python
def run_png_mesh_decay(png_path: Path, output_dir: Path, params: Simulation2DParams | None = None) -> dict[str, Any]:
    cfg = params or Simulation2DParams()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    inspection = inspect_png_phase_map(Path(png_path), output_dir / "input")
    if inspection.status != "success":
        return inspection.summary() | {"status": "failed", "stage": "input"}

    labels, scale = downsample_nearest(inspection.labels, cfg.max_grid_size)
    effective = Simulation2DParams(
        pixel_size_x_um=cfg.pixel_size_x_um * scale,
        pixel_size_y_um=cfg.pixel_size_y_um * scale,
        diffusion_um2_per_ms=cfg.diffusion_um2_per_ms,
        bulk_t2_ms=cfg.bulk_t2_ms,
        rho_solid_um_per_ms=cfg.rho_solid_um_per_ms,
        rho_gas_um_per_ms=cfg.rho_gas_um_per_ms,
        dt_ms=cfg.dt_ms,
        t_max_ms=cfg.t_max_ms,
        max_grid_size=cfg.max_grid_size,
        solver="triangular",
        mesh_bulk_size_um=cfg.mesh_bulk_size_um,
        mesh_boundary_size_um=cfg.mesh_boundary_size_um,
        mesh_max_points=cfg.mesh_max_points,
    )

    stem = Path(png_path).stem
    mesh_png = output_dir / "mesh" / f"{stem}_triangular_mesh.png"
    mesh_bms = output_dir / "mesh" / f"{stem}_triangular_mesh.bms"
    mesh_quality_csv = output_dir / "mesh" / f"{stem}_mesh_quality.csv"
    mesh_quality_hist = output_dir / "mesh" / f"{stem}_mesh_quality_histogram.png"
    curve_csv = output_dir / "decay" / f"{stem}_nmr_decay.csv"
    curve_png = output_dir / "decay" / f"{stem}_nmr_decay.png"
    decay_xlsx = output_dir / "decay" / f"{stem}__standard_decay.xlsx"

    time_ms, amplitude, mesh_summary = solve_decay_triangular(
        labels,
        effective,
        mesh_png,
        mesh_bms,
        mesh_quality_csv,
        mesh_quality_hist,
    )
    normalized = amplitude / max(float(amplitude[0]), 1e-30)
    curve_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"time_ms": time_ms, "signal": amplitude, "normalized_signal": normalized}).to_csv(curve_csv, index=False)
    save_decay_plot(time_ms, normalized, curve_png, title=f"{stem} T2 decay")
    write_standard_decay_workbook(decay_xlsx, time_ms, amplitude)

    result = {
        "status": "success",
        "stage": "decay",
        "input_path": str(Path(png_path).resolve()),
        "raw_shape": inspection.raw_shape,
        "cropped_shape": inspection.cropped_shape,
        "simulation_shape": [int(labels.shape[0]), int(labels.shape[1])],
        "downsample_scale": float(scale),
        "phase_counts": inspection.phase_counts,
        "params_used": asdict(effective),
        "cropped_png": str(inspection.cropped_png),
        "preview_png": str(inspection.preview_png),
        "mesh_png": str(mesh_png.resolve()),
        "pygimli_mesh_bms": str(mesh_bms.resolve()),
        "mesh_quality_csv": str(mesh_quality_csv.resolve()),
        "mesh_quality_histogram_png": str(mesh_quality_hist.resolve()),
        "curve_csv": str(curve_csv.resolve()),
        "curve_png": str(curve_png.resolve()),
        "standard_decay_xlsx": str(decay_xlsx.resolve()),
        "mesh_or_boundary_summary": mesh_summary,
        "time_point_count": int(len(time_ms)),
        "simulation_stages": {
            "geometry": [str(inspection.cropped_png), str(inspection.preview_png)],
            "mesh": [str(mesh_png), str(mesh_bms), str(mesh_quality_csv), str(mesh_quality_hist)],
            "decay": [str(curve_csv), str(curve_png), str(decay_xlsx)],
        },
    }
    result["summary_json"] = str(write_json_summary(output_dir / "simulation_2d_summary.json", result))
    return result
```

- [ ] **Step 5: Run pyGIMLi-gated test**

Run:

```powershell
pytest tests/test_simulation_2d.py::test_run_png_mesh_decay_writes_mesh_decay_and_workbook -q
```

Expected: PASS if pyGIMLi is installed, SKIPPED if not installed.

- [ ] **Step 6: Run all simulation backend tests**

Run:

```powershell
pytest tests/test_simulation_2d.py -q
```

Expected: PASS with possible pyGIMLi skip.

- [ ] **Step 7: Commit**

Run:

```powershell
git add t2_agent/simulation_2d.py tests/test_simulation_2d.py
git commit -m "feat: run 2d pygimli mesh decay"
```

---

### Task 4: Add Rule-Based 2D Geometry Input

**Files:**
- Modify: `t2_agent/simulation_2d.py`
- Modify: `tests/test_simulation_2d.py`

- [ ] **Step 1: Write rule-geometry tests**

Append to `tests/test_simulation_2d.py`:

```python
from t2_agent.simulation_2d import RuleGeometry2D, build_rule_geometry_labels


def test_build_rule_geometry_labels_can_make_uncoupled_two_pore_domain():
    geometry = RuleGeometry2D(coupled=False, canvas_width_px=80, canvas_height_px=50)

    labels = build_rule_geometry_labels(geometry)

    assert labels.shape == (50, 80)
    assert np.count_nonzero(labels == WATER) > 0
    assert np.count_nonzero(labels == SOLID) > 0
    mid_col = labels[:, labels.shape[1] // 2]
    assert np.count_nonzero(mid_col == WATER) == 0


def test_build_rule_geometry_labels_can_make_coupled_throat():
    geometry = RuleGeometry2D(coupled=True, canvas_width_px=80, canvas_height_px=50, throat_width_px=6)

    labels = build_rule_geometry_labels(geometry)

    mid_col = labels[:, labels.shape[1] // 2]
    assert np.count_nonzero(mid_col == WATER) > 0
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_simulation_2d.py::test_build_rule_geometry_labels_can_make_uncoupled_two_pore_domain tests/test_simulation_2d.py::test_build_rule_geometry_labels_can_make_coupled_throat -q
```

Expected: FAIL with missing `RuleGeometry2D`.

- [ ] **Step 3: Implement rule geometry dataclass and label generator**

Add this code to `t2_agent/simulation_2d.py`:

```python
@dataclass(frozen=True)
class RuleGeometry2D:
    coupled: bool = True
    canvas_width_px: int = 160
    canvas_height_px: int = 100
    large_pore_radius_px: int = 24
    small_pore_radius_px: int = 16
    throat_length_px: int = 30
    throat_width_px: int = 8


def build_rule_geometry_labels(geometry: RuleGeometry2D) -> np.ndarray:
    height = int(geometry.canvas_height_px)
    width = int(geometry.canvas_width_px)
    if height < 20 or width < 40:
        raise ValueError("Rule geometry canvas must be at least 40 x 20 pixels.")

    labels = np.full((height, width), SOLID, dtype=np.uint8)
    yy, xx = np.mgrid[0:height, 0:width]
    center_y = height // 2
    large_center_x = max(width // 3, int(geometry.large_pore_radius_px) + 2)
    small_center_x = min(2 * width // 3, width - int(geometry.small_pore_radius_px) - 3)
    large_mask = (xx - large_center_x) ** 2 + (yy - center_y) ** 2 <= int(geometry.large_pore_radius_px) ** 2
    small_mask = (xx - small_center_x) ** 2 + (yy - center_y) ** 2 <= int(geometry.small_pore_radius_px) ** 2
    labels[large_mask | small_mask] = WATER

    if geometry.coupled:
        throat_half = max(1, int(geometry.throat_width_px) // 2)
        x0 = min(large_center_x + int(geometry.large_pore_radius_px), small_center_x)
        x1 = max(small_center_x - int(geometry.small_pore_radius_px), large_center_x)
        labels[center_y - throat_half : center_y + throat_half + 1, x0 : x1 + 1] = WATER

    return labels


def save_rule_geometry_png(path: Path, geometry: RuleGeometry2D) -> Path:
    labels = build_rule_geometry_labels(geometry)
    save_phase_preview(labels, path)
    return path
```

- [ ] **Step 4: Add importable rule geometry run wrapper**

Add:

```python
def run_rule_geometry_mesh_decay(geometry: RuleGeometry2D, output_dir: Path, params: Simulation2DParams | None = None) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    phase_png = save_rule_geometry_png(output_dir / "input" / "rule_geometry_phase.png", geometry)
    result = run_png_mesh_decay(phase_png, output_dir, params)
    result["geometry_mode"] = "rule"
    result["rule_geometry"] = asdict(geometry)
    result["phase_png"] = str(phase_png)
    result["summary_json"] = str(write_json_summary(output_dir / "simulation_2d_summary.json", result))
    return result
```

- [ ] **Step 5: Run rule geometry tests**

Run:

```powershell
pytest tests/test_simulation_2d.py::test_build_rule_geometry_labels_can_make_uncoupled_two_pore_domain tests/test_simulation_2d.py::test_build_rule_geometry_labels_can_make_coupled_throat -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```powershell
git add t2_agent/simulation_2d.py tests/test_simulation_2d.py
git commit -m "feat: add rule geometry simulation input"
```

---

### Task 5: Expose Simulation Tools And Full Workflow

**Files:**
- Modify: `t2_agent/tools.py`
- Modify: `t2_agent/agent.py`
- Modify: `tests/test_agent_tool_loop.py`

- [ ] **Step 1: Write tool schema tests**

Append to `tests/test_agent_tool_loop.py`:

```python
def test_agent_tool_schema_exposes_2d_simulation_tools():
    specs = build_tool_specs()
    names = {item["function"]["name"] for item in specs}

    assert "inspect_2d_geometry_input" in names
    assert "run_2d_mesh_and_decay" in names
    assert "run_2d_simulation_full_workflow" in names


def test_execute_2d_mesh_and_decay_updates_context(tmp_path, monkeypatch):
    png_path = tmp_path / "phase.png"
    png_path.write_bytes(b"fake")
    decay_path = tmp_path / "decay.xlsx"
    decay_path.write_bytes(b"fake-xlsx")
    context = AgentRuntimeContext(workspace=tmp_path / "workspace", uploaded_path=png_path)

    def fake_run_png_mesh_decay(input_path, output_dir, params):
        return {
            "status": "success",
            "standard_decay_xlsx": str(decay_path),
            "mesh_png": str(tmp_path / "mesh.png"),
            "curve_png": str(tmp_path / "decay.png"),
            "simulation_stages": {"mesh": [str(tmp_path / "mesh.png")], "decay": [str(tmp_path / "decay.png"), str(decay_path)]},
        }

    monkeypatch.setattr("t2_agent.tools.run_png_mesh_decay", fake_run_png_mesh_decay)

    result = execute_agent_tool("run_2d_mesh_and_decay", {"geometry_mode": "png"}, context)

    assert result.status == "success"
    assert context.repaired_path == decay_path
    assert context.simulation_decay_path == decay_path
    assert result.summary["simulation_stages"]["decay"][-1] == str(decay_path)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_agent_tool_loop.py::test_agent_tool_schema_exposes_2d_simulation_tools tests/test_agent_tool_loop.py::test_execute_2d_mesh_and_decay_updates_context -q
```

Expected: FAIL because schemas and context field are not implemented.

- [ ] **Step 3: Import simulation helpers in tools**

In `t2_agent/tools.py`, add:

```python
from .simulation_2d import (
    RuleGeometry2D,
    Simulation2DParams,
    inspect_png_phase_map,
    run_png_mesh_decay,
    run_rule_geometry_mesh_decay,
)
```

- [ ] **Step 4: Add parameter builders in tools**

Add these helper functions to `t2_agent/tools.py`:

```python
def _simulation_params_from_args(args: dict[str, Any]) -> Simulation2DParams:
    return Simulation2DParams(
        pixel_size_x_um=float(args.get("pixel_size_x_um", args.get("pixel_size_um", 1.0))),
        pixel_size_y_um=float(args.get("pixel_size_y_um", args.get("pixel_size_um", 1.0))),
        diffusion_um2_per_ms=float(args.get("diffusion_um2_per_ms", 2.0)),
        bulk_t2_ms=float(args.get("bulk_t2_ms", 3000.0)),
        rho_solid_um_per_ms=float(args.get("rho_solid_um_per_ms", 0.005)),
        rho_gas_um_per_ms=float(args.get("rho_gas_um_per_ms", 0.0)),
        dt_ms=float(args.get("dt_ms", 5.0)),
        t_max_ms=float(args.get("t_max_ms", 1500.0)),
        max_grid_size=args.get("max_grid_size", 500),
        solver="triangular",
        mesh_bulk_size_um=float(args.get("mesh_bulk_size_um", 8.0)),
        mesh_boundary_size_um=float(args.get("mesh_boundary_size_um", 2.0)),
        mesh_max_points=int(args.get("mesh_max_points", 25000)),
    )


def _rule_geometry_from_args(args: dict[str, Any]) -> RuleGeometry2D:
    return RuleGeometry2D(
        coupled=bool(args.get("coupled", True)),
        canvas_width_px=int(args.get("canvas_width_px", 160)),
        canvas_height_px=int(args.get("canvas_height_px", 100)),
        large_pore_radius_px=int(args.get("large_pore_radius_px", 24)),
        small_pore_radius_px=int(args.get("small_pore_radius_px", 16)),
        throat_length_px=int(args.get("throat_length_px", 30)),
        throat_width_px=int(args.get("throat_width_px", 8)),
    )
```

- [ ] **Step 5: Add tool functions**

Add to `t2_agent/tools.py`:

```python
def inspect_2d_geometry_input(input_path: Path | None, output_dir: Path, params: dict[str, Any] | None = None, language: str = "中文") -> AgentToolResult:
    params = params or {}
    mode = str(params.get("geometry_mode", "png")).lower()
    try:
        if mode == "rule":
            geometry = _rule_geometry_from_args(params)
            return AgentToolResult(
                "success",
                "规则二维几何参数已读取。" if not _is_english(language) else "Rule-based 2D geometry parameters were read.",
                summary={"stage": "geometry", "geometry_mode": "rule", "rule_geometry": geometry.__dict__},
            )
        if input_path is None:
            return AgentToolResult("failed", "请先上传 PNG 相图。" if not _is_english(language) else "Please upload a PNG phase map first.", error="missing_upload")
        inspection = inspect_png_phase_map(Path(input_path), Path(output_dir) / "geometry")
        artifacts = [str(inspection.cropped_png), str(inspection.preview_png)] if inspection.cropped_png.exists() else []
        return AgentToolResult(
            "success" if inspection.status == "success" else "failed",
            inspection.message,
            artifacts=artifacts,
            summary=inspection.summary() | {"stage": "geometry", "geometry_mode": "png", "simulation_stages": {"geometry": artifacts}},
            error=inspection.error,
        )
    except Exception as exc:
        return AgentToolResult("failed", "二维几何输入检查失败。" if not _is_english(language) else "2D geometry inspection failed.", error=str(exc))


def run_2d_mesh_and_decay(input_path: Path | None, output_dir: Path, params: dict[str, Any] | None = None, language: str = "中文") -> AgentToolResult:
    params = params or {}
    mode = str(params.get("geometry_mode", "png")).lower()
    try:
        sim_params = _simulation_params_from_args(params)
        if mode == "rule":
            result = run_rule_geometry_mesh_decay(_rule_geometry_from_args(params), Path(output_dir), sim_params)
        else:
            if input_path is None:
                return AgentToolResult("failed", "请先上传 PNG 相图。" if not _is_english(language) else "Please upload a PNG phase map first.", error="missing_upload")
            result = run_png_mesh_decay(Path(input_path), Path(output_dir), sim_params)
        artifacts = [str(value) for key, value in result.items() if key.endswith(("_png", "_csv", "_xlsx", "_bms", "_json")) and value]
        status = "success" if result.get("status") == "success" else "failed"
        message = "2D 网格划分和 NMR 衰减求解完成。" if status == "success" and not _is_english(language) else "2D mesh generation and NMR decay solve completed."
        if status != "success":
            message = "2D 网格划分或衰减求解失败。" if not _is_english(language) else "2D mesh generation or decay solve failed."
        return AgentToolResult(status, message, artifacts=artifacts, summary=result, error=result.get("error"))
    except Exception as exc:
        return AgentToolResult("failed", "2D 网格划分或衰减求解失败。" if not _is_english(language) else "2D mesh generation or decay solve failed.", error=str(exc))
```

- [ ] **Step 6: Add context field**

In `t2_agent/agent.py`, add to `AgentRuntimeContext`:

```python
simulation_decay_path: Path | None = None
```

- [ ] **Step 7: Add tool imports and execution branches**

In `t2_agent/agent.py`, import:

```python
inspect_2d_geometry_input,
run_2d_mesh_and_decay,
```

Then add `execute_agent_tool` branches:

```python
if name == "inspect_2d_geometry_input":
    result = inspect_2d_geometry_input(context.uploaded_path, context.workspace / "simulation_2d", args, language=response_language)
    context.results.append(result)
    return result

if name == "run_2d_mesh_and_decay":
    result = run_2d_mesh_and_decay(context.uploaded_path, context.workspace / "simulation_2d", args, language=response_language)
    context.results.append(result)
    standard_decay = result.summary.get("standard_decay_xlsx")
    if result.status == "success" and standard_decay:
        context.simulation_decay_path = Path(standard_decay)
        context.repaired_path = Path(standard_decay)
    return result
```

- [ ] **Step 8: Add tool schemas**

In `build_tool_specs()`, add schemas for `inspect_2d_geometry_input` and `run_2d_mesh_and_decay` with these parameters:

```python
"geometry_mode": {"type": "string", "enum": ["png", "rule"]},
"pixel_size_um": {"type": "number"},
"pixel_size_x_um": {"type": "number"},
"pixel_size_y_um": {"type": "number"},
"diffusion_um2_per_ms": {"type": "number"},
"bulk_t2_ms": {"type": "number"},
"rho_solid_um_per_ms": {"type": "number"},
"rho_gas_um_per_ms": {"type": "number"},
"dt_ms": {"type": "number"},
"t_max_ms": {"type": "number"},
"mesh_bulk_size_um": {"type": "number"},
"mesh_boundary_size_um": {"type": "number"},
"mesh_max_points": {"type": "integer"},
"coupled": {"type": "boolean"},
"canvas_width_px": {"type": "integer"},
"canvas_height_px": {"type": "integer"},
"large_pore_radius_px": {"type": "integer"},
"small_pore_radius_px": {"type": "integer"},
"throat_width_px": {"type": "integer"}
```

- [ ] **Step 9: Run focused tests**

Run:

```powershell
pytest tests/test_agent_tool_loop.py::test_agent_tool_schema_exposes_2d_simulation_tools tests/test_agent_tool_loop.py::test_execute_2d_mesh_and_decay_updates_context -q
```

Expected: PASS.

- [ ] **Step 10: Commit**

Run:

```powershell
git add t2_agent/tools.py t2_agent/agent.py tests/test_agent_tool_loop.py
git commit -m "feat: expose 2d simulation tools"
```

---

### Task 6: Add Full Simulation Workflow Tool

**Files:**
- Modify: `t2_agent/tools.py`
- Modify: `t2_agent/agent.py`
- Modify: `tests/test_agent_tool_loop.py`

- [ ] **Step 1: Write full workflow unit test with monkeypatches**

Append to `tests/test_agent_tool_loop.py`:

```python
def test_full_2d_simulation_workflow_reuses_existing_inversion_tools(tmp_path, monkeypatch):
    png_path = tmp_path / "phase.png"
    png_path.write_bytes(b"fake")
    decay_path = tmp_path / "decay.xlsx"
    spectrum_path = tmp_path / "spectrum.xlsx"
    context = AgentRuntimeContext(workspace=tmp_path / "workspace", uploaded_path=png_path)

    def fake_mesh(input_path, output_dir, params, language="中文"):
        return AgentToolResult("success", "mesh ok", artifacts=[str(decay_path)], summary={"standard_decay_xlsx": str(decay_path), "simulation_stages": {"decay": [str(decay_path)]}})

    def fake_lcurve(input_workbook, output_dir, params, language="中文"):
        return AgentToolResult("success", "lcurve ok", artifacts=[str(spectrum_path)], summary={"spectrum_xlsx": str(spectrum_path)})

    monkeypatch.setattr("t2_agent.agent.run_2d_mesh_and_decay", fake_mesh)
    monkeypatch.setattr("t2_agent.agent.run_lcurve", fake_lcurve)

    result = execute_agent_tool("run_2d_simulation_full_workflow", {"geometry_mode": "png", "num_bins": 30, "alpha_count": 6}, context)

    assert result.status == "success"
    assert context.repaired_path == decay_path
    assert context.spectrum_path == spectrum_path
    assert any(item.summary.get("spectrum_xlsx") == str(spectrum_path) for item in context.results)
```

- [ ] **Step 2: Run test to verify failure**

Run:

```powershell
pytest tests/test_agent_tool_loop.py::test_full_2d_simulation_workflow_reuses_existing_inversion_tools -q
```

Expected: FAIL with unknown tool.

- [ ] **Step 3: Add execution branch for full workflow**

In `t2_agent/agent.py`, add an `execute_agent_tool` branch:

```python
if name == "run_2d_simulation_full_workflow":
    mesh = run_2d_mesh_and_decay(context.uploaded_path, context.workspace / "simulation_2d", args, language=response_language)
    context.results.append(mesh)
    if mesh.status != "success":
        return mesh
    standard_decay = mesh.summary.get("standard_decay_xlsx")
    if not standard_decay:
        return AgentToolResult("failed", "2D simulation did not produce a standard decay workbook.", error="missing_simulation_decay")
    context.simulation_decay_path = Path(standard_decay)
    context.repaired_path = Path(standard_decay)

    if args.get("regularization") is not None:
        inversion = run_fixed_nnls(
            context.repaired_path,
            context.workspace / "simulation_2d" / "nnls",
            {
                "time_to_ms_scale": 1.0,
                "regularization": float(args["regularization"]),
                "t2_min_ms": float(args.get("t2_min_ms", 1.0)),
                "t2_max_ms": float(args.get("t2_max_ms", 1e4)),
                "num_bins": int(args.get("num_bins", 200)),
            },
            language=response_language,
        )
    else:
        inversion = run_lcurve(
            context.repaired_path,
            context.workspace / "simulation_2d" / "lcurve",
            {
                "time_to_ms_scale": 1.0,
                "t2_min_ms": float(args.get("t2_min_ms", 1e-2)),
                "t2_max_ms": float(args.get("t2_max_ms", 1e5)),
                "num_bins": int(args.get("num_bins", 200)),
                "alpha_min": float(args.get("alpha_min", 1e-6)),
                "alpha_max": float(args.get("alpha_max", 1e2)),
                "alpha_count": int(args.get("alpha_count", 60)),
            },
            language=response_language,
        )
    context.results.append(inversion)
    if inversion.status == "success" and "spectrum_xlsx" in inversion.summary:
        context.spectrum_path = Path(inversion.summary["spectrum_xlsx"])

    if bool(args.get("run_gaussian", False)) and context.spectrum_path is not None:
        gaussian = run_gaussian_peaks(context.spectrum_path, context.workspace / "simulation_2d" / "gaussian", {"peak_count": int(args.get("peak_count", 2))}, language=response_language)
        context.results.append(gaussian)

    return AgentToolResult(
        "success" if inversion.status == "success" else "failed",
        "2D NMR 模拟和 T2 反演流程完成。" if not _is_english(response_language) else "2D NMR simulation and T2 inversion workflow completed.",
        artifacts=[artifact for result in context.results for artifact in result.artifacts],
        summary={"stage": "full_workflow", "simulation_decay_xlsx": str(context.repaired_path), "spectrum_xlsx": str(context.spectrum_path) if context.spectrum_path else None},
        error=inversion.error,
    )
```

- [ ] **Step 4: Add schema for `run_2d_simulation_full_workflow`**

In `build_tool_specs()`, add a schema with the same simulation parameters as `run_2d_mesh_and_decay`, plus:

```python
"regularization": {"type": "number"},
"t2_min_ms": {"type": "number"},
"t2_max_ms": {"type": "number"},
"num_bins": {"type": "integer"},
"alpha_min": {"type": "number"},
"alpha_max": {"type": "number"},
"alpha_count": {"type": "integer"},
"run_gaussian": {"type": "boolean"},
"peak_count": {"type": "integer", "minimum": 1, "maximum": 8}
```

- [ ] **Step 5: Run focused test**

Run:

```powershell
pytest tests/test_agent_tool_loop.py::test_full_2d_simulation_workflow_reuses_existing_inversion_tools -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```powershell
git add t2_agent/agent.py tests/test_agent_tool_loop.py
git commit -m "feat: add full 2d simulation workflow tool"
```

---

### Task 7: Update Agent Intent, Guidance, And User-Facing Prompt

**Files:**
- Modify: `t2_agent/guidance.py`
- Modify: `t2_agent/agent.py`
- Modify: `streamlit_app.py`
- Modify: `tests/test_t2_agent.py`
- Modify: `tests/test_agent_tool_loop.py`

- [ ] **Step 1: Write guidance tests**

Add to `tests/test_t2_agent.py`:

```python
def test_guidance_detects_2d_png_simulation_intent():
    plan = infer_requested_plan("上传红黄PNG，帮我做二维NMR模拟并T2反演")

    assert plan.workflow == "simulation_2d_png"
    assert plan.needs_gaussian is False


def test_guidance_detects_rule_geometry_simulation_intent():
    plan = infer_requested_plan("设置规则几何，两个孔耦合，跑一次完整二维模拟")

    assert plan.workflow == "simulation_2d_rule"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_t2_agent.py::test_guidance_detects_2d_png_simulation_intent tests/test_t2_agent.py::test_guidance_detects_rule_geometry_simulation_intent -q
```

Expected: FAIL because guidance does not know simulation intents yet.

- [ ] **Step 3: Update intent inference**

In `t2_agent/guidance.py`, update `infer_requested_plan()` after creating `plan`:

```python
simulation_intent = any(token in text for token in ("模拟", "正演", "网格", "几何", "pygimli", "PNG", "png", "phase map", "phase-map", "NMR simulation"))
png_intent = any(token in text for token in ("PNG", "png", "图片", "图像", "相图", "phase map", "phase-map"))
rule_intent = any(token in text for token in ("规则", "几何", "耦合", "喉道", "尺寸", "rule", "geometry"))

if simulation_intent:
    plan.workflow = "simulation_2d_full"
    if png_intent:
        plan.workflow = "simulation_2d_png"
    if rule_intent and not png_intent:
        plan.workflow = "simulation_2d_rule"
    plan.user_is_unsure = any(token in text for token in ("默认", "测试", "你来", "自动", "完整"))
```

Then update `build_parameter_guidance()` so simulation workflows return guidance that explains:

```text
二维模拟会先检查几何/PNG，再用 pyGIMLi 三角网格生成网格，随后求解 NMR/T2 衰减曲线，并把得到的时域曲线送入现有 T2 反演。测试运行可使用默认物理参数，但这些参数需要在正式解释前由用户确认。
```

- [ ] **Step 4: Update system prompt**

In `t2_agent/agent.py`, replace:

```python
"You are an NMR T2 inversion agent that can call real tools. "
```

with:

```python
"You are an NMR 2D simulation and T2 inversion agent that can call real tools. "
```

Add these instructions into `system_content`:

```python
"For 2D simulation requests, use the simulation tools instead of spreadsheet validation tools. "
"If the user uploads a PNG or asks for red/yellow phase-map simulation, call inspect_2d_geometry_input and then run_2d_mesh_and_decay or run_2d_simulation_full_workflow. "
"For the first version, only 2D simulation is supported, and mesh generation must use pyGIMLi triangular meshing. "
"When the user asks for the whole simulation flow, call run_2d_simulation_full_workflow so mesh, decay, T2 inversion, and optional Gaussian decomposition are connected. "
"When the user only asks for T2 inversion, keep using the existing T2 workbook tools and do not force simulation. "
```

- [ ] **Step 5: Update welcome copy**

In `streamlit_app.py`, update Chinese and English `WELCOME_MESSAGES` to say the app can now:

```text
- 做二维 NMR 模拟：规则几何或红黄白 PNG 相图 -> pyGIMLi 网格 -> T2 衰减 -> T2 反演
- 仍然支持只做 T2 反演
```

Remove the older boundary line that says it does not do mesh generation or Bloch-Torrey forward simulation. Replace it with:

```text
- 第一版模拟仅支持 2D；不做 CT 分割、3D、T2-T2 或 D-T2
```

- [ ] **Step 6: Run guidance and prompt tests**

Run:

```powershell
pytest tests/test_t2_agent.py::test_guidance_detects_2d_png_simulation_intent tests/test_t2_agent.py::test_guidance_detects_rule_geometry_simulation_intent tests/test_agent_tool_loop.py::test_agent_loop_can_request_english_response_language -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

Run:

```powershell
git add t2_agent/guidance.py t2_agent/agent.py streamlit_app.py tests/test_t2_agent.py tests/test_agent_tool_loop.py
git commit -m "feat: teach agent 2d simulation intents"
```

---

### Task 8: Add Streamlit PNG Upload And Staged Result Rendering

**Files:**
- Modify: `streamlit_app.py`
- Modify: `t2_agent/i18n.py`
- Modify: `tests/test_streamlit_rendering.py`

- [ ] **Step 1: Write staged rendering helper tests**

Add to `tests/test_streamlit_rendering.py`:

```python
from streamlit_app import group_simulation_stage_artifacts


def test_group_simulation_stage_artifacts_uses_summary_stage_map(tmp_path):
    mesh = tmp_path / "mesh.png"
    decay = tmp_path / "decay.png"
    mesh.write_bytes(b"mesh")
    decay.write_bytes(b"decay")
    result = AgentToolResult(
        "success",
        "ok",
        artifacts=[str(mesh), str(decay)],
        summary={"simulation_stages": {"mesh": [str(mesh)], "decay": [str(decay)]}},
    )

    grouped = group_simulation_stage_artifacts(result)

    assert grouped["mesh"] == [mesh]
    assert grouped["decay"] == [decay]
```

- [ ] **Step 2: Run test to verify failure**

Run:

```powershell
pytest tests/test_streamlit_rendering.py::test_group_simulation_stage_artifacts_uses_summary_stage_map -q
```

Expected: FAIL with missing helper.

- [ ] **Step 3: Add stage grouping helper**

In `streamlit_app.py`, add:

```python
SIMULATION_STAGE_ORDER = ["geometry", "mesh", "decay", "inversion", "gaussian", "report"]


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
```

- [ ] **Step 4: Update `render_result`**

In `render_result`, after the structured summary expander and before generic image rendering, add:

```python
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
```

- [ ] **Step 5: Add i18n labels**

In `t2_agent/i18n.py`, add Chinese keys:

```python
"simulation_stage_geometry": "几何 / 相图阶段",
"simulation_stage_mesh": "网格阶段",
"simulation_stage_decay": "时域衰减阶段",
"simulation_stage_inversion": "T2 反演阶段",
"simulation_stage_gaussian": "Gaussian 分峰阶段",
"simulation_stage_report": "报告阶段",
"png_upload_hint": "PNG 相图需使用红色=液体/水相、黄色=固体、白色=外部背景；第一版只支持 2D 模拟。",
```

Add English keys:

```python
"simulation_stage_geometry": "Geometry / Phase Map",
"simulation_stage_mesh": "Mesh",
"simulation_stage_decay": "Time-Domain Decay",
"simulation_stage_inversion": "T2 Inversion",
"simulation_stage_gaussian": "Gaussian Peaks",
"simulation_stage_report": "Report",
"png_upload_hint": "PNG phase maps must use red=liquid/water, yellow=solid, white=outside background. The first simulation version supports 2D only.",
```

- [ ] **Step 6: Allow PNG uploads**

In `streamlit_app.py`, update the uploader type list:

```python
type=["xlsx", "xls", "csv", "pea", "txt", "dat", "png"]
```

Update the upload hint block:

```python
        if context and context.uploaded_path:
            active_suffix = Path(context.uploaded_path).suffix.lower()
            st.info(t(language, "current_file", filename=Path(context.uploaded_path).name))
            st.caption(t(language, "png_upload_hint") if active_suffix == ".png" else t(language, "upload_hint"))
```

- [ ] **Step 7: Run rendering tests**

Run:

```powershell
pytest tests/test_streamlit_rendering.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

Run:

```powershell
git add streamlit_app.py t2_agent/i18n.py tests/test_streamlit_rendering.py
git commit -m "feat: render 2d simulation stages"
```

---

### Task 9: Documentation And End-To-End Verification

**Files:**
- Modify: `README.md`
- Modify: `tests/test_simulation_2d.py`
- Modify: `tests/test_agent_tool_loop.py`

- [ ] **Step 1: Update README**

In `README.md`, add a section after "What It Does":

```markdown
## 2D NMR Simulation Workflow

The app can also run a first-version 2D NMR simulation workflow:

```text
rule geometry or red/yellow/white PNG -> pyGIMLi triangular mesh -> T2 decay solve -> T2 inversion
```

PNG phase maps must use:

- red for liquid/water pore space;
- yellow for solid matrix;
- white for outside/background.

White borders are cropped automatically. The first version supports 2D only and
does not perform CT segmentation, 3D simulation, T2-T2, or D-T2.
```

- [ ] **Step 2: Add full fake-client test**

Add to `tests/test_agent_tool_loop.py`:

```python
def test_agent_loop_can_call_full_2d_simulation_tool(tmp_path):
    png_path = tmp_path / "phase.png"
    png_path.write_bytes(b"fake-png")
    context = AgentRuntimeContext(workspace=tmp_path / "workspace", uploaded_path=png_path)
    fake_client = FakeClient(
        [
            _message(tool_calls=[_tool_call("run_2d_simulation_full_workflow", {"geometry_mode": "png", "num_bins": 30, "alpha_count": 6})]),
            _message(content="二维 NMR 模拟和 T2 反演已经完成。"),
        ]
    )

    result = run_deepseek_agent_turn(
        api_key="test-key",
        model="deepseek-v4-flash",
        thinking_enabled=False,
        user_message="请用这个红黄PNG跑完整二维NMR模拟并做T2反演",
        context=context,
        prior_messages=[],
        client=fake_client,
    )

    assert "二维 NMR 模拟" in result.assistant_message
    assert result.trace[1]["tool_name"] == "run_2d_simulation_full_workflow"
```

Use monkeypatches if this test tries to run real pyGIMLi; the purpose is function-calling routing, not numerical solving.

- [ ] **Step 3: Run focused tests**

Run:

```powershell
pytest tests/test_simulation_2d.py tests/test_agent_tool_loop.py tests/test_streamlit_rendering.py -q
```

Expected: PASS, with pyGIMLi-dependent tests skipped if pyGIMLi is unavailable.

- [ ] **Step 4: Run current full test suite**

Run:

```powershell
pytest -q
```

Expected: PASS, with pyGIMLi-dependent tests skipped if pyGIMLi is unavailable.

- [ ] **Step 5: Run a local Streamlit smoke check**

Start the app:

```powershell
streamlit run streamlit_app.py --server.headless true --server.port 8501
```

Expected:

- app starts without import errors;
- uploader accepts `.png`;
- welcome copy mentions first-version 2D NMR simulation;
- existing Excel-only T2 workflow still appears available.

Stop the server with Ctrl+C after checking.

- [ ] **Step 6: Commit**

Run:

```powershell
git add README.md tests/test_agent_tool_loop.py
git commit -m "docs: document 2d nmr simulation workflow"
```

---

## Self-Review Checklist

- Spec coverage:
  - Standalone T2 inversion remains intact through untouched existing tools and regression tests.
  - PNG phase-map input is covered by `inspect_png_phase_map`, PNG upload support, and tests.
  - White-border cropping is covered by `sample_bbox` and the PNG inspection test.
  - pyGIMLi-only meshing is covered by `run_png_mesh_decay` and pyGIMLi-gated tests.
  - Rule geometry is covered by `RuleGeometry2D`, `build_rule_geometry_labels`, and tests.
  - Decay-to-T2 handoff is covered by standard decay workbook export and full workflow tests.
  - Stage-by-stage right-column rendering is covered by `group_simulation_stage_artifacts`.

- Placeholder scan:
  - The plan avoids unresolved markers and vague "add handling" steps.
  - Each task names exact files, commands, expected outcomes, and commit points.

- Type consistency:
  - `Simulation2DParams`, `RuleGeometry2D`, `run_png_mesh_decay`, `run_rule_geometry_mesh_decay`, `inspect_2d_geometry_input`, and `run_2d_mesh_and_decay` have consistent names across tasks.
  - `AgentRuntimeContext.simulation_decay_path` is set when a standard simulation decay workbook is produced.
  - `summary["simulation_stages"]` is the single contract used by tools and Streamlit rendering.
