"""Whitelisted local tools for the Streamlit T2 agent."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .models import AgentToolResult


REPO_ROOT = Path(__file__).resolve().parents[1]
T2PROCESS_ROOT = REPO_ROOT / "T2process"
if str(T2PROCESS_ROOT) not in sys.path:
    sys.path.insert(0, str(T2PROCESS_ROOT))

from nmr_t2.config import GaussianConfig, LCurveConfig, NnlsConfig, PlotConfig  # noqa: E402
from nmr_t2.io_utils import cell_to_float, parse_time_cell, safe_token  # noqa: E402
from nmr_t2.pipelines import (  # noqa: E402
    run_gaussian_decomposition_on_spectrum_workbook,
    run_lcurve_workbook,
    run_nnls_workbook,
    run_plotting_workbook_pair,
)


def _read_first_table(path: Path) -> pd.DataFrame | None:
    try:
        if path.suffix.lower() == ".csv":
            return pd.read_csv(path)
        if path.suffix.lower() in {".xlsx", ".xls"}:
            return pd.read_excel(path)
    except Exception:
        return None
    return None


def _find_artifact(results: list[AgentToolResult], contains: str, suffixes: tuple[str, ...]) -> Path | None:
    for result in results:
        for artifact in result.artifacts:
            path = Path(artifact)
            if contains in path.name and path.suffix.lower() in suffixes and path.exists():
                return path
    return None


def _safe_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except Exception:
        return None
    return parsed if np.isfinite(parsed) else None


def interpret_results(results: list[AgentToolResult], output_dir: Path) -> AgentToolResult:
    """Summarize generated T2 artifacts into a user-facing interpretation."""

    try:
        lines = ["# T2 结果解释", ""]
        summary: dict[str, Any] = {}

        lcurve_summary_path = _find_artifact(results, "lcurve_summary", (".csv", ".xlsx"))
        lcurve_spectrum_path = _find_artifact(results, "lcurve_spectrum", (".xlsx", ".xls"))
        nnls_summary_path = _find_artifact(results, "nnls_summary", (".csv", ".xlsx"))
        nnls_spectrum_path = _find_artifact(results, "nnls_spectrum", (".xlsx", ".xls"))
        gaussian_summary_path = _find_artifact(results, "gaussian_summary", (".csv", ".xlsx"))

        inversion_summary_path = lcurve_summary_path or nnls_summary_path
        spectrum_path = lcurve_spectrum_path or nnls_spectrum_path

        if inversion_summary_path:
            inversion_summary = _read_first_table(inversion_summary_path)
            if inversion_summary is not None and not inversion_summary.empty:
                row = inversion_summary.iloc[0].to_dict()
                best_regularization = _safe_float(row.get("best_regularization", row.get("regularization")))
                residual_norm = _safe_float(row.get("best_residual_norm", row.get("residual_norm")))
                roughness_norm = _safe_float(row.get("best_roughness_norm", row.get("roughness_norm")))
                summary.update(
                    {
                        "inversion_summary_file": str(inversion_summary_path),
                        "best_regularization": best_regularization,
                        "residual_norm": residual_norm,
                        "roughness_norm": roughness_norm,
                    }
                )
                lines.append("## 反演质量与平滑因子")
                if best_regularization is not None:
                    lines.append(f"- 最佳平滑因子约为 `{best_regularization:.4g}`。它是 L-curve 在拟合误差和谱线平滑之间选出的折中值。")
                if residual_norm is not None:
                    lines.append(f"- 残差范数约为 `{residual_norm:.4g}`，数值越小说明拟合越贴近数据，但不能单独用它判断结果是否最好。")
                if roughness_norm is not None:
                    lines.append(f"- 粗糙度范数约为 `{roughness_norm:.4g}`，用于衡量 T2 谱是否过度起伏。")
                lines.append("")

        if spectrum_path:
            sheets = pd.read_excel(spectrum_path, sheet_name=None)
            first_sheet_name, spectrum_df = next(iter(sheets.items()))
            t2_col = "t2_ms" if "t2_ms" in spectrum_df.columns else spectrum_df.columns[0]
            amp_col = "amplitude" if "amplitude" in spectrum_df.columns else spectrum_df.columns[1]
            t2 = pd.to_numeric(spectrum_df[t2_col], errors="coerce").to_numpy(dtype=float)
            amp = pd.to_numeric(spectrum_df[amp_col], errors="coerce").to_numpy(dtype=float)
            mask = np.isfinite(t2) & np.isfinite(amp) & (t2 > 0)
            t2 = t2[mask]
            amp = amp[mask]
            if t2.size and amp.size:
                max_idx = int(np.argmax(amp))
                total_area = float(np.trapezoid(amp, np.log10(t2))) if t2.size > 1 else float(amp[max_idx])
                short_fraction = float(np.trapezoid(amp[t2 < 10], np.log10(t2[t2 < 10])) / total_area) if np.sum(t2 < 10) > 1 and total_area > 0 else 0.0
                mid_mask = (t2 >= 10) & (t2 < 1000)
                mid_fraction = float(np.trapezoid(amp[mid_mask], np.log10(t2[mid_mask])) / total_area) if np.sum(mid_mask) > 1 and total_area > 0 else 0.0
                long_fraction = max(0.0, 1.0 - short_fraction - mid_fraction) if total_area > 0 else 0.0
                summary.update(
                    {
                        "spectrum_file": str(spectrum_path),
                        "signal_name": first_sheet_name,
                        "main_peak_t2_ms": float(t2[max_idx]),
                        "main_peak_amplitude": float(amp[max_idx]),
                        "short_t2_fraction_lt_10ms": short_fraction,
                        "middle_t2_fraction_10_1000ms": mid_fraction,
                        "long_t2_fraction_ge_1000ms": long_fraction,
                    }
                )
                lines.append("## T2 谱解释")
                lines.append(f"- 主峰位置约在 `{float(t2[max_idx]):.4g} ms`，这是当前谱中幅值最高的 T2 组分。")
                lines.append(f"- 短 T2（<10 ms）面积占比约 `{short_fraction:.1%}`，通常更偏束缚流体、小孔或表面弛豫强的组分。")
                lines.append(f"- 中等 T2（10-1000 ms）面积占比约 `{mid_fraction:.1%}`，通常对应较可动的孔隙流体。")
                lines.append(f"- 长 T2（>=1000 ms）面积占比约 `{long_fraction:.1%}`，可能对应更自由的流体或长弛豫尾部。")
                lines.append("")

        if gaussian_summary_path:
            gaussian_summary = _read_first_table(gaussian_summary_path)
            if gaussian_summary is not None and not gaussian_summary.empty:
                lines.append("## Gaussian 分峰解释")
                peak_rows = []
                for _, row in gaussian_summary.iterrows():
                    peak_rows.append(
                        {
                            "peak_id": int(row.get("peak_id", len(peak_rows) + 1)),
                            "position_ms": _safe_float(row.get("position_ms")),
                            "area_fraction": _safe_float(row.get("area_fraction")),
                        }
                    )
                summary["gaussian_peaks"] = peak_rows
                for peak in peak_rows:
                    position = peak["position_ms"]
                    fraction = peak["area_fraction"]
                    if position is not None and fraction is not None:
                        lines.append(f"- 峰 {peak['peak_id']}：位置约 `{position:.4g} ms`，面积占比约 `{fraction:.1%}`。")
                lines.append("")

        if len(lines) <= 2:
            return AgentToolResult("failed", "还没有足够的反演结果可解释。请先运行 L-curve 或 NNLS。", error="missing_result_artifacts")

        lines.extend(
            [
                "## 需要注意",
                "- 这些解释基于数学反演结果，最终物理含义需要结合样品岩性、孔隙结构和实验条件判断。",
                "- 如果要区分具体孔隙组分，建议继续做 Gaussian 分峰并比较不同峰的面积占比。",
            ]
        )
        output_path = Path(output_dir) / "interpretation.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")

        message = "\n".join(line for line in lines if line != "")[:3000]
        return AgentToolResult("success", message, artifacts=[str(output_path)], summary=summary)
    except Exception as exc:
        return AgentToolResult("failed", "结果解释失败。", error=str(exc))


def _profile_columns(table: pd.DataFrame) -> list[dict[str, Any]]:
    layout_candidates: list[dict[str, Any]] = []
    for col_idx in range(table.shape[1]):
        label = _column_label(table, col_idx)
        numeric = _numeric_column(table, col_idx)
        finite = numeric[np.isfinite(numeric)]
        positive = finite[finite > 0]
        layout_candidates.append(
            {
                "excel_index": int(col_idx + 1),
                "label": label,
                "finite_numeric_count": int(finite.size),
                "positive_numeric_count": int(positive.size),
                "min": float(np.min(finite)) if finite.size else None,
                "max": float(np.max(finite)) if finite.size else None,
                "first_numeric_values": [float(value) for value in finite[:5]],
                "monotonic_increasing_score": _monotonic_increasing_score(numeric),
            }
        )
    return layout_candidates


def inspect_workbook_schema(input_workbook: Path, preview_rows: int = 8) -> AgentToolResult:
    """Return workbook preview and column profiles for AI reasoning."""

    try:
        input_path = Path(input_workbook)
        if not input_path.exists():
            return AgentToolResult("failed", f"找不到上传文件：{input_path}", error="file_not_found")

        workbook = pd.ExcelFile(input_path)
        sheet_name = workbook.sheet_names[0]
        table = pd.read_excel(input_path, sheet_name=sheet_name, header=None, dtype=object)
        preview = table.head(int(preview_rows)).where(pd.notnull(table.head(int(preview_rows))), None).values.tolist()
        profiles = _profile_columns(table)
        message = (
            f"已读取工作簿结构。第一个 sheet 为 {sheet_name}，形状为 {table.shape[0]} 行 x {table.shape[1]} 列。"
            "我会根据列名、单调递增性和数值范围判断哪一列是时间/T2，哪些列是信号幅值。"
        )
        return AgentToolResult(
            "success",
            message,
            summary={
                "sheet_names": workbook.sheet_names,
                "active_sheet": sheet_name,
                "shape": [int(table.shape[0]), int(table.shape[1])],
                "preview_rows": preview,
                "column_profiles": profiles,
            },
        )
    except Exception as exc:
        return AgentToolResult("failed", "工作簿结构检查失败。", error=str(exc))


def _as_artifacts(paths: dict[str, Path] | list[Path]) -> list[str]:
    if isinstance(paths, dict):
        values = list(paths.values())
    else:
        values = paths

    artifacts: list[str] = []
    for value in values:
        path = Path(value)
        if path.is_dir():
            artifacts.extend(str(item) for item in sorted(path.glob("*")) if item.is_file())
        else:
            artifacts.append(str(path))
    return artifacts


def _add_pair_plot_artifacts(
    *,
    raw_decay_workbook: Path,
    spectrum_workbook: Path | None,
    output_dir: Path,
    artifacts: list[str],
    summary: dict[str, Any],
) -> None:
    """Append decay + T2 spectrum figures without failing the inversion result."""

    if spectrum_workbook is None:
        return

    try:
        paired = run_plotting_workbook_pair(
            Path(raw_decay_workbook),
            Path(spectrum_workbook),
            Path(output_dir) / "paired_plots",
            plot_config=PlotConfig(),
            time_to_ms_scale=1.0,
        )
    except Exception as exc:
        summary["paired_plot_warning"] = str(exc)
        return

    pair_artifacts = _as_artifacts(list(paired.values()))
    artifacts.extend(pair_artifacts)
    summary["paired_plot_count"] = len(pair_artifacts)


def _read_raw_table(input_workbook: Path) -> pd.DataFrame:
    return pd.read_excel(input_workbook, header=None, dtype=object)


def _column_label(table: pd.DataFrame, column_idx: int) -> str:
    if table.empty:
        return f"col_{column_idx + 1}"
    first = table.iat[0, column_idx]
    if isinstance(first, str) and cell_to_float(first) != cell_to_float(first):
        return first.strip() or f"col_{column_idx + 1}"
    return f"col_{column_idx + 1}"


def _numeric_column(table: pd.DataFrame, column_idx: int) -> np.ndarray:
    return np.asarray([cell_to_float(value) for value in table.iloc[:, column_idx]], dtype=float)


def _monotonic_increasing_score(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    if finite.size < 3:
        return 0.0
    diffs = np.diff(finite)
    return float(np.sum(diffs > 0) / diffs.size)


def _infer_layout(table: pd.DataFrame) -> dict[str, Any]:
    """Infer time/T2 column and signal columns from headers plus numeric shape."""

    candidates: list[dict[str, Any]] = []
    for col_idx in range(table.shape[1]):
        label = _column_label(table, col_idx)
        label_key = label.lower()
        numeric = _numeric_column(table, col_idx)
        finite = numeric[np.isfinite(numeric)]
        positive_count = int(np.sum(finite > 0))
        finite_count = int(finite.size)
        increasing = _monotonic_increasing_score(numeric)

        time_score = finite_count * 0.01 + increasing * 50.0
        if any(token in label_key for token in ("time", "t2", "时间")):
            time_score += 120.0
        if any(token in label_key for token in ("peak", "amplitude", "signal", "幅", "峰")):
            time_score -= 80.0
        if positive_count < 2:
            time_score -= 100.0

        candidates.append(
            {
                "index": col_idx,
                "label": label,
                "numeric": numeric,
                "finite_count": finite_count,
                "positive_count": positive_count,
                "increasing_score": increasing,
                "time_score": time_score,
            }
        )

    if not candidates:
        raise ValueError("Workbook has no columns.")

    time_candidate = max(candidates, key=lambda item: item["time_score"])
    if time_candidate["positive_count"] < 2:
        raise ValueError("No valid time/T2 column was detected.")

    signal_candidates = [
        item
        for item in candidates
        if item["index"] != time_candidate["index"] and item["finite_count"] > 0
    ]
    if not signal_candidates:
        raise ValueError("No valid signal columns were detected.")

    return {
        "time_column": time_candidate,
        "signal_columns": signal_candidates,
        "all_columns": candidates,
    }


def _parsed_rows(table: pd.DataFrame) -> tuple[list[float], list[list[float]]]:
    matrix = table.values
    times: list[float] = []
    signals: list[list[float]] = []

    for row_idx in range(matrix.shape[0]):
        ok, time_value = parse_time_cell(matrix[row_idx, 0])
        if not ok:
            continue
        row_signals = [cell_to_float(matrix[row_idx, col_idx]) for col_idx in range(1, matrix.shape[1])]
        times.append(float(time_value))
        signals.append(row_signals)
    return times, signals


def _parsed_rows_by_layout(table: pd.DataFrame, layout: dict[str, Any]) -> tuple[list[float], list[list[float]]]:
    matrix = table.values
    time_col = int(layout["time_column"]["index"])
    signal_cols = [int(item["index"]) for item in layout["signal_columns"]]
    times: list[float] = []
    signals: list[list[float]] = []

    for row_idx in range(matrix.shape[0]):
        ok, time_value = parse_time_cell(matrix[row_idx, time_col])
        if not ok:
            continue
        row_signals = [cell_to_float(matrix[row_idx, col_idx]) for col_idx in signal_cols]
        times.append(float(time_value))
        signals.append(row_signals)
    return times, signals


def _recommend_time_scale(time_values: np.ndarray) -> tuple[float, str]:
    positive = time_values[np.isfinite(time_values) & (time_values > 0)]
    if positive.size == 0:
        return 1.0, "没有足够的正时间点，暂时按 ms 处理。"

    max_time = float(np.max(positive))
    diffs = np.diff(np.sort(positive))
    median_step = float(np.median(diffs[diffs > 0])) if np.any(diffs > 0) else np.nan

    if max_time <= 10 and (not np.isfinite(median_step) or median_step < 0.1):
        return 1000.0, "时间数值整体很小，更像是秒；建议乘以 1000 转成 ms。"
    return 1.0, "时间范围更像已经是 ms；建议保持 1:1。"


def _infer_data_kind(input_workbook: Path, table: pd.DataFrame) -> str:
    first_row = " ".join(str(value).lower() for value in table.iloc[0].tolist()) if not table.empty else ""
    name = input_workbook.name.lower()
    if "spectrum" in name or "t2" in first_row:
        return "spectrum"
    return "decay"


def validate_workbook(input_workbook: Path) -> AgentToolResult:
    """Inspect an uploaded workbook and recommend safe defaults."""

    try:
        input_path = Path(input_workbook)
        if not input_path.exists():
            return AgentToolResult("failed", f"找不到上传文件：{input_path}", error="file_not_found")

        table = _read_raw_table(input_path)
        if table.empty or table.shape[1] < 2:
            return AgentToolResult(
                "failed",
                "Excel 至少需要两列：第一列为时间或 T2，后续列为信号幅度。",
                error="not_enough_columns",
            )

        try:
            layout = _infer_layout(table)
        except ValueError as exc:
            error_text = str(exc)
            if "No valid time" in error_text:
                return AgentToolResult("failed", "没有检测到有效时间/T2 数值列。", error="no_valid_time")
            if "No valid signal" in error_text:
                return AgentToolResult("failed", "没有检测到有效信号列。请确认数据中包含数值幅度。", error="no_valid_signal")
            return AgentToolResult("failed", "Excel 数据布局识别失败。", error=error_text)
        times, signals = _parsed_rows_by_layout(table, layout)
        if not times:
            return AgentToolResult("failed", "没有检测到有效时间/T2 数值列。", error="no_valid_time")

        time_values = np.asarray(times, dtype=float)
        signal_matrix = np.asarray(signals, dtype=float)
        finite_signal_mask = np.any(np.isfinite(signal_matrix), axis=0)
        signal_column_count = int(np.sum(finite_signal_mask))
        if signal_column_count == 0:
            return AgentToolResult("failed", "没有检测到有效信号列。请确认数据中包含数值幅度。", error="no_valid_signal")

        scale, scale_reason = _recommend_time_scale(time_values)
        data_kind = _infer_data_kind(input_path, table)
        invalid_signal_cells = int(np.size(signal_matrix) - np.sum(np.isfinite(signal_matrix)))
        valid_rows = int(np.sum(np.isfinite(time_values) & (time_values > 0)))
        time_column = layout["time_column"]
        signal_columns = layout["signal_columns"]
        column_order_issue = "time_not_first_column" if int(time_column["index"]) != 0 else "none"

        summary: dict[str, Any] = {
            "data_kind": data_kind,
            "row_count": int(table.shape[0]),
            "column_count": int(table.shape[1]),
            "valid_time_rows": valid_rows,
            "signal_column_count": signal_column_count,
            "recommended_time_to_ms_scale": float(scale),
            "time_scale_reason": scale_reason,
            "invalid_signal_cells": invalid_signal_cells,
            "time_column_excel_index": int(time_column["index"] + 1),
            "time_column_label": str(time_column["label"]),
            "signal_excel_columns": [int(item["index"] + 1) for item in signal_columns],
            "signal_column_labels": [str(item["label"]) for item in signal_columns],
            "column_order_issue": column_order_issue,
            "valid_signal_excel_columns": [int(item["index"] + 1) for item in signal_columns],
            "column_profiles": _profile_columns(table),
        }
        order_note = ""
        if column_order_issue != "none":
            order_note = (
                f"注意：我检测到时间/T2 列不是第一列，而是在第 {summary['time_column_excel_index']} 列 "
                f"({summary['time_column_label']})；第 {summary['signal_excel_columns']} 列更像信号幅值 "
                f"({', '.join(summary['signal_column_labels'])})。后续会自动重排为 time_ms + signal。"
            )
        message = (
            f"已读取 Excel。检测到第 {summary['time_column_excel_index']} 列 "
            f"({summary['time_column_label']}) 是时间/T2，共 {valid_rows} 个有效点；"
            f"检测到 {signal_column_count} 个有效信号列：{', '.join(summary['signal_column_labels'])}。"
            f"{scale_reason}{order_note}"
        )
        return AgentToolResult("success", message, summary=summary)
    except Exception as exc:
        return AgentToolResult("failed", "Excel 数据诊断失败。", error=str(exc))


def repair_workbook(input_workbook: Path, output_dir: Path, time_to_ms_scale: float = 1.0) -> AgentToolResult:
    """Write a standardized workbook with `time_ms` plus numeric signal columns."""

    try:
        table = _read_raw_table(Path(input_workbook))
        try:
            layout = _infer_layout(table)
        except ValueError as exc:
            error_text = str(exc)
            if "No valid time" in error_text:
                return AgentToolResult("failed", "无法修复：没有有效时间/T2 数值列。", error="no_valid_time")
            if "No valid signal" in error_text:
                return AgentToolResult("failed", "无法修复：没有有效信号列。", error="no_valid_signal")
            return AgentToolResult("failed", "无法修复：数据布局识别失败。", error=error_text)
        times, signals = _parsed_rows_by_layout(table, layout)
        if not times:
            return AgentToolResult("failed", "无法修复：没有有效时间/T2 数值列。", error="no_valid_time")

        time_values = np.asarray(times, dtype=float)
        signal_matrix = np.asarray(signals, dtype=float)
        positive_time = np.isfinite(time_values) & (time_values > 0)
        time_values = time_values[positive_time] * float(time_to_ms_scale)
        signal_matrix = signal_matrix[positive_time, :]

        finite_signal_mask = np.any(np.isfinite(signal_matrix), axis=0)
        if not np.any(finite_signal_mask):
            return AgentToolResult("failed", "无法修复：没有有效信号列。", error="no_valid_signal")

        signal_matrix = signal_matrix[:, finite_signal_mask]
        data = {"time_ms": time_values}
        signal_columns = [layout["signal_columns"][idx] for idx, keep in enumerate(finite_signal_mask) if keep]
        for idx, signal_col in enumerate(signal_columns):
            data[str(signal_col["label"])] = signal_matrix[:, idx]

        output_path = Path(output_dir) / f"{safe_token(Path(input_workbook).stem)}__standardized.xlsx"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(data).to_excel(output_path, index=False)
        return AgentToolResult(
            "success",
            "已生成标准化 Excel：第一列为 time_ms，后续列为有效信号。",
            artifacts=[str(output_path)],
            summary={
                "standardized_workbook": str(output_path),
                "time_to_ms_scale_applied": float(time_to_ms_scale),
                "signal_column_count": int(signal_matrix.shape[1]),
                "source_time_column_excel_index": int(layout["time_column"]["index"] + 1),
                "source_signal_excel_columns": [int(item["index"] + 1) for item in signal_columns],
            },
        )
    except Exception as exc:
        return AgentToolResult("failed", "Excel 自动修复失败。", error=str(exc))


def run_lcurve(input_workbook: Path, output_dir: Path, params: dict[str, Any] | None = None) -> AgentToolResult:
    """Run L-curve inversion and return exported artifacts."""

    params = params or {}
    try:
        cfg = LCurveConfig(
            num_bins=int(params.get("num_bins", 200)),
            t2_min_ms=float(params.get("t2_min_ms", 1e-2)),
            t2_max_ms=float(params.get("t2_max_ms", 1e5)),
            alpha_min=float(params.get("alpha_min", 1e-6)),
            alpha_max=float(params.get("alpha_max", 1e2)),
            alpha_count=int(params.get("alpha_count", 60)),
            min_points_after_trim=int(params.get("min_points_after_trim", 10)),
        )
        result = run_lcurve_workbook(
            Path(input_workbook),
            Path(output_dir),
            config=cfg,
            plot_config=PlotConfig(),
            time_to_ms_scale=float(params.get("time_to_ms_scale", 1.0)),
            trim_from_peak=bool(params.get("trim_from_peak", True)),
        )
        artifacts = _as_artifacts(result)
        summary = {key: str(value) for key, value in result.items()}
        spectrum_path = Path(result["spectrum_xlsx"]) if "spectrum_xlsx" in result else None
        _add_pair_plot_artifacts(
            raw_decay_workbook=Path(input_workbook),
            spectrum_workbook=spectrum_path,
            output_dir=Path(output_dir),
            artifacts=artifacts,
            summary=summary,
        )
        return AgentToolResult(
            "success",
            "L-curve 反演完成，已自动选择平滑因子并导出 T2 谱、指标表和图像。",
            artifacts=artifacts,
            summary=summary,
        )
    except Exception as exc:
        return AgentToolResult("failed", "L-curve 反演失败。", error=str(exc))


def run_fixed_nnls(input_workbook: Path, output_dir: Path, params: dict[str, Any] | None = None) -> AgentToolResult:
    """Run fixed-regularization NNLS inversion."""

    params = params or {}
    try:
        regularization = float(params.get("regularization", 1.0))
        cfg = NnlsConfig(
            num_bins=int(params.get("num_bins", 200)),
            regularization=regularization,
            t2_min_ms=float(params.get("t2_min_ms", 1.0)),
            t2_max_ms=float(params.get("t2_max_ms", 1e4)),
            min_points_after_trim=int(params.get("min_points_after_trim", 10)),
        )
        result = run_nnls_workbook(
            Path(input_workbook),
            Path(output_dir),
            config=cfg,
            time_to_ms_scale=float(params.get("time_to_ms_scale", 1.0)),
            trim_from_peak=bool(params.get("trim_from_peak", True)),
        )
        artifacts = _as_artifacts(result)
        summary = {key: str(value) for key, value in result.items()} | {"regularization": regularization}
        spectrum_path = Path(result["spectrum_xlsx"]) if "spectrum_xlsx" in result else None
        _add_pair_plot_artifacts(
            raw_decay_workbook=Path(input_workbook),
            spectrum_workbook=spectrum_path,
            output_dir=Path(output_dir),
            artifacts=artifacts,
            summary=summary,
        )
        return AgentToolResult(
            "success",
            f"固定 NNLS 反演完成，使用平滑因子 {regularization:g}。",
            artifacts=artifacts,
            summary=summary,
        )
    except Exception as exc:
        return AgentToolResult("failed", "固定 NNLS 反演失败。", error=str(exc))


def plot_decay_spectrum(
    raw_decay_workbook: Path,
    spectrum_workbook: Path,
    output_dir: Path,
    params: dict[str, Any] | None = None,
) -> AgentToolResult:
    """Generate paired decay/T2 spectrum plots."""

    params = params or {}
    try:
        result = run_plotting_workbook_pair(
            Path(raw_decay_workbook),
            Path(spectrum_workbook),
            Path(output_dir),
            plot_config=PlotConfig(),
            time_to_ms_scale=float(params.get("time_to_ms_scale", 1.0)),
        )
        return AgentToolResult(
            "success",
            "衰减曲线和 T2 谱配对图已生成。",
            artifacts=_as_artifacts(list(result.values())),
            summary={"figure_count": len(result)},
        )
    except Exception as exc:
        return AgentToolResult("failed", "配对图生成失败。", error=str(exc))


def run_gaussian_peaks(spectrum_workbook: Path, output_dir: Path, params: dict[str, Any] | None = None) -> AgentToolResult:
    """Run Gaussian peak decomposition on a spectrum workbook."""

    params = params or {}
    try:
        peak_count = int(params.get("peak_count", 2))
        result = run_gaussian_decomposition_on_spectrum_workbook(
            Path(spectrum_workbook),
            Path(output_dir),
            config=GaussianConfig(peak_count=peak_count),
            plot_config=PlotConfig(),
        )
        return AgentToolResult(
            "success",
            f"Gaussian 分峰完成，使用 {peak_count} 个峰。",
            artifacts=_as_artifacts(result),
            summary={key: str(value) for key, value in result.items()} | {"peak_count": peak_count},
        )
    except Exception as exc:
        return AgentToolResult("failed", "Gaussian 分峰失败。", error=str(exc))


def generate_report(
    output_dir: Path,
    *,
    user_goal: str,
    validation: AgentToolResult,
    workflow_results: list[AgentToolResult],
    parameter_notes: str,
) -> AgentToolResult:
    """Generate a Chinese Markdown report from tool results."""

    try:
        output_path = Path(output_dir) / "report.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            "# T2 反演智能体报告",
            "",
            "## 用户目标",
            user_goal.strip() or "用户未提供额外目标，按默认 T2 反演流程处理。",
            "",
            "## 数据诊断",
            validation.message,
            "",
            "```text",
            str(validation.summary),
            "```",
            "",
            "## 参数解释与选择",
            parameter_notes,
            "",
            "## 工具运行结果",
        ]

        for idx, result in enumerate(workflow_results, start=1):
            lines.extend(
                [
                    f"### 步骤 {idx}",
                    f"- 状态：{result.status}",
                    f"- 说明：{result.message}",
                    f"- 输出数量：{len(result.artifacts)}",
                ]
            )
            if result.error:
                lines.append(f"- 错误：{result.error}")
            if result.summary:
                lines.extend(["", "```text", str(result.summary), "```"])
            lines.append("")

        lines.extend(
            [
                "## 注意事项",
                "- 平滑因子越小，越容易贴合噪声；越大，越容易抹平真实小峰。",
                "- L-curve 适合初次分析，但最终解释仍建议结合样品背景和实验条件。",
                "- Gaussian 分峰是谱形解释工具，不等同于唯一的物理组分划分。",
            ]
        )

        output_path.write_text("\n".join(lines), encoding="utf-8")
        return AgentToolResult("success", "中文 Markdown 报告已生成。", artifacts=[str(output_path)], summary={"report": str(output_path)})
    except Exception as exc:
        return AgentToolResult("failed", "报告生成失败。", error=str(exc))
