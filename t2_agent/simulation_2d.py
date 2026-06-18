"""2D NMR simulation helpers for phase-map and rule-geometry workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg", force=True)

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
        return PngInspection(
            "failed",
            str(exc),
            input_path,
            [],
            [],
            {},
            np.zeros((0, 0), dtype=np.uint8),
            cropped_png,
            preview_png,
            "empty_sample",
        )
    except Exception as exc:
        return PngInspection(
            "failed",
            "PNG phase-map inspection failed.",
            input_path,
            [],
            [],
            {},
            np.zeros((0, 0), dtype=np.uint8),
            cropped_png,
            preview_png,
            str(exc),
        )


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
    frame = pd.DataFrame(
        {
            "time_ms": np.asarray(time_ms, dtype=float),
            "signal": np.asarray(signal, dtype=float),
        }
    )
    frame.to_excel(output_path, index=False)
    return output_path


def write_json_summary(path: Path, payload: dict[str, Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return output_path
