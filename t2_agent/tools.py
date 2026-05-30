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


def _is_english(language: str) -> bool:
    return language.lower().startswith("english")


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


def interpret_results(results: list[AgentToolResult], output_dir: Path, language: str = "中文") -> AgentToolResult:
    """Summarize generated T2 artifacts into a user-facing interpretation."""

    try:
        english = _is_english(language)
        lines = ["# T2 Result Interpretation" if english else "# T2 结果解释", ""]
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
                lines.append("## Inversion Quality and Smoothing Factor" if english else "## 反演质量与平滑因子")
                if best_regularization is not None:
                    if english:
                        lines.append(f"- The best smoothing factor is about `{best_regularization:.4g}`. This is the L-curve compromise between fitting error and spectrum smoothness.")
                    else:
                        lines.append(f"- 最佳平滑因子约为 `{best_regularization:.4g}`。它是 L-curve 在拟合误差和谱线平滑之间选出的折中值。")
                if residual_norm is not None:
                    if english:
                        lines.append(f"- The residual norm is about `{residual_norm:.4g}`. Smaller values mean the fit is closer to the data, but this alone does not prove the result is best.")
                    else:
                        lines.append(f"- 残差范数约为 `{residual_norm:.4g}`，数值越小说明拟合越贴近数据，但不能单独用它判断结果是否最好。")
                if roughness_norm is not None:
                    if english:
                        lines.append(f"- The roughness norm is about `{roughness_norm:.4g}`. It measures how strongly the T2 spectrum fluctuates.")
                    else:
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
                lines.append("## T2 Spectrum Interpretation" if english else "## T2 谱解释")
                if english:
                    lines.append(f"- The main peak is around `{float(t2[max_idx]):.4g} ms`, which is the strongest T2 component in the current spectrum.")
                    lines.append(f"- The short-T2 area fraction (<10 ms) is about `{short_fraction:.1%}`. This often indicates bound fluid, small pores, or strong surface relaxation.")
                    lines.append(f"- The middle-T2 area fraction (10-1000 ms) is about `{mid_fraction:.1%}`. This often corresponds to more mobile pore fluid.")
                    lines.append(f"- The long-T2 area fraction (>=1000 ms) is about `{long_fraction:.1%}`. This may indicate freer fluid or a long relaxation tail.")
                else:
                    lines.append(f"- 主峰位置约在 `{float(t2[max_idx]):.4g} ms`，这是当前谱中幅值最高的 T2 组分。")
                    lines.append(f"- 短 T2（<10 ms）面积占比约 `{short_fraction:.1%}`，通常更偏束缚流体、小孔或表面弛豫强的组分。")
                    lines.append(f"- 中等 T2（10-1000 ms）面积占比约 `{mid_fraction:.1%}`，通常对应较可动的孔隙流体。")
                    lines.append(f"- 长 T2（>=1000 ms）面积占比约 `{long_fraction:.1%}`，可能对应更自由的流体或长弛豫尾部。")
                lines.append("")

        if gaussian_summary_path:
            gaussian_summary = _read_first_table(gaussian_summary_path)
            if gaussian_summary is not None and not gaussian_summary.empty:
                lines.append("## Gaussian Peak Interpretation" if english else "## Gaussian 分峰解释")
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
                        if english:
                            lines.append(f"- Peak {peak['peak_id']}: position about `{position:.4g} ms`, area fraction about `{fraction:.1%}`.")
                        else:
                            lines.append(f"- 峰 {peak['peak_id']}：位置约 `{position:.4g} ms`，面积占比约 `{fraction:.1%}`。")
                lines.append("")

        if len(lines) <= 2:
            message = "There are not enough inversion results to interpret yet. Run L-curve or NNLS first." if english else "还没有足够的反演结果可解释。请先运行 L-curve 或 NNLS。"
            return AgentToolResult("failed", message, error="missing_result_artifacts")

        if english:
            lines.extend(
                [
                    "## Notes",
                    "- These interpretations are based on mathematical inversion results. The final physical meaning should be judged together with lithology, pore structure, and experimental conditions.",
                    "- To distinguish specific pore components, continue with Gaussian peak decomposition and compare the area fractions of different peaks.",
                ]
            )
        else:
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
        message = "Result interpretation failed." if _is_english(language) else "结果解释失败。"
        return AgentToolResult("failed", message, error=str(exc))


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


def inspect_workbook_schema(input_workbook: Path, preview_rows: int = 8, language: str = "中文") -> AgentToolResult:
    """Return workbook preview and column profiles for AI reasoning."""

    try:
        english = _is_english(language)
        input_path = Path(input_workbook)
        if not input_path.exists():
            message = f"Uploaded file not found: {input_path}" if english else f"找不到上传文件：{input_path}"
            return AgentToolResult("failed", message, error="file_not_found")

        workbook = pd.ExcelFile(input_path)
        sheet_name = workbook.sheet_names[0]
        table = pd.read_excel(input_path, sheet_name=sheet_name, header=None, dtype=object)
        preview = table.head(int(preview_rows)).where(pd.notnull(table.head(int(preview_rows))), None).values.tolist()
        profiles = _profile_columns(table)
        preliminary_data_kind = "unknown"
        try:
            layout = _infer_layout(table)
            times, signals = _parsed_rows_by_layout(table, layout)
            preliminary_data_kind = _infer_data_kind(
                input_path,
                table,
                layout=layout,
                time_values=np.asarray(times, dtype=float),
                signal_matrix=np.asarray(signals, dtype=float),
            )
        except Exception:
            preliminary_data_kind = "unknown"
        if english:
            message = (
                f"Workbook structure loaded. The first sheet is {sheet_name}, with {table.shape[0]} rows x {table.shape[1]} columns. "
                f"Preliminary data kind: {preliminary_data_kind}. I will identify the time or T2-axis column and signal-amplitude columns from labels, monotonicity, numeric ranges, preview rows, and curve shape."
            )
        else:
            kind_label = {"decay": "原始衰减数据", "spectrum": "T2 谱表"}.get(preliminary_data_kind, "暂不确定")
            message = (
                f"已读取工作簿结构。第一个 sheet 为 {sheet_name}，形状为 {table.shape[0]} 行 x {table.shape[1]} 列。"
                f"初步判断为：{kind_label}。我会根据列名、单调性、数值范围、预览行和曲线形态综合判断。"
            )
        return AgentToolResult(
            "success",
            message,
            summary={
                "sheet_names": workbook.sheet_names,
                "active_sheet": sheet_name,
                "shape": [int(table.shape[0]), int(table.shape[1])],
                "preliminary_data_kind": preliminary_data_kind,
                "preview_rows": preview,
                "column_profiles": profiles,
            },
        )
    except Exception as exc:
        message = "Workbook structure inspection failed." if _is_english(language) else "工作簿结构检查失败。"
        return AgentToolResult("failed", message, error=str(exc))


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


def _curve_shape_data_kind(time_values: np.ndarray, signal_matrix: np.ndarray) -> str | None:
    """Classify decay vs spectrum from curve shape when the data are clear."""

    if time_values.size < 8 or signal_matrix.size == 0:
        return None

    finite_column_counts = np.sum(np.isfinite(signal_matrix), axis=0)
    if finite_column_counts.size == 0 or int(np.max(finite_column_counts)) < 8:
        return None

    signal_idx = int(np.argmax(finite_column_counts))
    x = np.asarray(time_values, dtype=float)
    y = np.asarray(signal_matrix[:, signal_idx], dtype=float)
    mask = np.isfinite(x) & np.isfinite(y) & (x > 0)
    x = x[mask]
    y = y[mask]
    if x.size < 8:
        return None

    order = np.argsort(x)
    x = x[order]
    y = y[order]
    diffs = np.diff(y)
    if diffs.size == 0:
        return None

    y_min = float(np.min(y))
    y_max = float(np.max(y))
    y_range = y_max - y_min
    if not np.isfinite(y_range) or y_range <= max(abs(y_max), 1.0) * 1e-9:
        return None

    n = int(y.size)
    max_idx = int(np.argmax(y))
    decreasing_score = float(np.sum(diffs < 0) / diffs.size)
    near_start_peak = max_idx <= max(2, int(0.08 * n))
    end_drop_fraction = (float(y[max_idx]) - float(np.median(y[-max(3, n // 10) :]))) / y_range
    if near_start_peak and decreasing_score >= 0.62 and end_drop_fraction >= 0.25:
        return "decay"

    if max(2, int(0.05 * n)) <= max_idx <= min(n - 3, int(0.95 * n)):
        before = np.diff(y[: max_idx + 1])
        after = np.diff(y[max_idx:])
        before_increasing = float(np.sum(before > 0) / before.size) if before.size else 0.0
        after_decreasing = float(np.sum(after < 0) / after.size) if after.size else 0.0
        edge_level = max(float(np.median(y[: max(3, n // 10)])), float(np.median(y[-max(3, n // 10) :])))
        prominence_fraction = (float(y[max_idx]) - edge_level) / y_range
        if before_increasing >= 0.55 and after_decreasing >= 0.55 and prominence_fraction >= 0.18:
            return "spectrum"

    return None


def _infer_data_kind(
    input_workbook: Path,
    table: pd.DataFrame,
    layout: dict[str, Any] | None = None,
    time_values: np.ndarray | None = None,
    signal_matrix: np.ndarray | None = None,
) -> str:
    first_row_values = [str(value).strip().lower() for value in table.iloc[0].tolist()] if not table.empty else []
    first_row = " ".join(first_row_values)
    name = input_workbook.name.lower()

    if time_values is None or signal_matrix is None:
        try:
            inferred_layout = layout or _infer_layout(table)
            times, signals = _parsed_rows_by_layout(table, inferred_layout)
            time_values = np.asarray(times, dtype=float)
            signal_matrix = np.asarray(signals, dtype=float)
        except Exception:
            time_values = None
            signal_matrix = None

    if time_values is not None and signal_matrix is not None:
        shape_kind = _curve_shape_data_kind(time_values, signal_matrix)
        if shape_kind is not None:
            return shape_kind

    has_t2_axis_label = any(
        token in first_row
        for token in ("t2", "t₂", "relaxation", "弛豫")
    )
    has_spectrum_amplitude_label = any(
        token in first_row
        for token in ("amplitude", "spectrum", "intensity", "distribution", "peak", "谱", "幅", "峰")
    )
    if has_t2_axis_label and has_spectrum_amplitude_label:
        return "spectrum"
    if "spectrum" in name and has_spectrum_amplitude_label:
        return "spectrum"
    return "decay"


def _workbook_data_kind(input_workbook: Path) -> str:
    """Best-effort workbook kind classification for tool-level safety checks."""

    try:
        table = _read_raw_table(Path(input_workbook))
        if table.empty:
            return "unknown"
        return _infer_data_kind(Path(input_workbook), table)
    except Exception:
        return "unknown"


def _spectrum_input_error(language: str) -> AgentToolResult:
    english = _is_english(language)
    message = (
        "This workbook looks like an existing T2 spectrum, not raw decay data. I will not run T2 inversion on it; use Gaussian peak decomposition directly, or confirm if you intended to upload raw decay data."
        if english
        else "这个工作簿看起来是已有 T2 谱表，不是原始衰减数据。我不会把它再做 T2 反演；如果你的目标是分峰，可以直接做 Gaussian 分峰，若本意是上传原始衰减数据，请确认文件。"
    )
    return AgentToolResult("failed", message, error="spectrum_input_not_decay")


def validate_workbook(input_workbook: Path, language: str = "中文") -> AgentToolResult:
    """Inspect an uploaded workbook and recommend safe defaults."""

    try:
        english = _is_english(language)
        input_path = Path(input_workbook)
        if not input_path.exists():
            message = f"Uploaded file not found: {input_path}" if english else f"找不到上传文件：{input_path}"
            return AgentToolResult("failed", message, error="file_not_found")

        table = _read_raw_table(input_path)
        if table.empty or table.shape[1] < 2:
            message = "Excel needs at least two columns: the first for time or T2, followed by signal-amplitude columns." if english else "Excel 至少需要两列：第一列为时间或 T2，后续列为信号幅度。"
            return AgentToolResult(
                "failed",
                message,
                error="not_enough_columns",
            )

        try:
            layout = _infer_layout(table)
        except ValueError as exc:
            error_text = str(exc)
            if "No valid time" in error_text:
                message = "No valid numeric time/T2 column was detected." if english else "没有检测到有效时间/T2 数值列。"
                return AgentToolResult("failed", message, error="no_valid_time")
            if "No valid signal" in error_text:
                message = "No valid signal column was detected. Please confirm the data contains numeric amplitudes." if english else "没有检测到有效信号列。请确认数据中包含数值幅度。"
                return AgentToolResult("failed", message, error="no_valid_signal")
            message = "Excel layout recognition failed." if english else "Excel 数据布局识别失败。"
            return AgentToolResult("failed", message, error=error_text)
        times, signals = _parsed_rows_by_layout(table, layout)
        if not times:
            message = "No valid numeric time/T2 column was detected." if english else "没有检测到有效时间/T2 数值列。"
            return AgentToolResult("failed", message, error="no_valid_time")

        time_values = np.asarray(times, dtype=float)
        signal_matrix = np.asarray(signals, dtype=float)
        finite_signal_mask = np.any(np.isfinite(signal_matrix), axis=0)
        signal_column_count = int(np.sum(finite_signal_mask))
        if signal_column_count == 0:
            message = "No valid signal column was detected. Please confirm the data contains numeric amplitudes." if english else "没有检测到有效信号列。请确认数据中包含数值幅度。"
            return AgentToolResult("failed", message, error="no_valid_signal")

        scale, scale_reason = _recommend_time_scale(time_values)
        if english:
            scale_reason = (
                "The time values are very small and look like seconds; I recommend multiplying by 1000 to convert to ms."
                if scale == 1000.0
                else "The time range looks like it is already in ms; I recommend keeping a 1:1 scale."
            )
        data_kind = _infer_data_kind(input_path, table, layout=layout, time_values=time_values, signal_matrix=signal_matrix)
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
            if english:
                order_note = (
                    f" Note: the detected time/T2 column is not the first column; it is column {summary['time_column_excel_index']} "
                    f"({summary['time_column_label']}). Columns {summary['signal_excel_columns']} look more like signal amplitudes "
                    f"({', '.join(summary['signal_column_labels'])}). I will reorder the data into time_ms + signal."
                )
            else:
                order_note = (
                    f"注意：我检测到时间/T2 列不是第一列，而是在第 {summary['time_column_excel_index']} 列 "
                    f"({summary['time_column_label']})；第 {summary['signal_excel_columns']} 列更像信号幅值 "
                    f"({', '.join(summary['signal_column_labels'])})。后续会自动重排为 time_ms + signal。"
                )
        kind_note = ""
        if data_kind == "spectrum":
            kind_note = (
                " This looks like an existing T2 spectrum, so inversion should be skipped; Gaussian peak decomposition can run directly if that is your goal."
                if english
                else "这看起来是已有 T2 谱表，应跳过反演；如果目标是分峰，可以直接做 Gaussian 分峰。"
            )
        axis_label = "T2 axis" if data_kind == "spectrum" else "time column"
        axis_label_cn = "T2 轴" if data_kind == "spectrum" else "时间列"
        if english:
            message = (
                f"Excel loaded. Column {summary['time_column_excel_index']} ({summary['time_column_label']}) appears to be the {axis_label}, "
                f"with {valid_rows} valid points. Detected {signal_column_count} valid signal columns: {', '.join(summary['signal_column_labels'])}. "
                f"{scale_reason}{order_note}{kind_note}"
            )
        else:
            message = (
                f"已读取 Excel。检测到第 {summary['time_column_excel_index']} 列 "
                f"({summary['time_column_label']}) 是{axis_label_cn}，共 {valid_rows} 个有效点；"
                f"检测到 {signal_column_count} 个有效信号列：{', '.join(summary['signal_column_labels'])}。"
                f"{scale_reason}{order_note}{kind_note}"
            )
        return AgentToolResult("success", message, summary=summary)
    except Exception as exc:
        message = "Excel data diagnosis failed." if _is_english(language) else "Excel 数据诊断失败。"
        return AgentToolResult("failed", message, error=str(exc))


def repair_workbook(input_workbook: Path, output_dir: Path, time_to_ms_scale: float = 1.0, language: str = "中文") -> AgentToolResult:
    """Write a standardized workbook with `time_ms` plus numeric signal columns."""

    try:
        english = _is_english(language)
        table = _read_raw_table(Path(input_workbook))
        if _infer_data_kind(Path(input_workbook), table) == "spectrum":
            return _spectrum_input_error(language)
        try:
            layout = _infer_layout(table)
        except ValueError as exc:
            error_text = str(exc)
            if "No valid time" in error_text:
                message = "Cannot repair: no valid numeric time/T2 column was detected." if english else "无法修复：没有有效时间/T2 数值列。"
                return AgentToolResult("failed", message, error="no_valid_time")
            if "No valid signal" in error_text:
                message = "Cannot repair: no valid signal column was detected." if english else "无法修复：没有有效信号列。"
                return AgentToolResult("failed", message, error="no_valid_signal")
            message = "Cannot repair: data layout recognition failed." if english else "无法修复：数据布局识别失败。"
            return AgentToolResult("failed", message, error=error_text)
        times, signals = _parsed_rows_by_layout(table, layout)
        if not times:
            message = "Cannot repair: no valid numeric time/T2 column was detected." if english else "无法修复：没有有效时间/T2 数值列。"
            return AgentToolResult("failed", message, error="no_valid_time")

        time_values = np.asarray(times, dtype=float)
        signal_matrix = np.asarray(signals, dtype=float)
        positive_time = np.isfinite(time_values) & (time_values > 0)
        time_values = time_values[positive_time] * float(time_to_ms_scale)
        signal_matrix = signal_matrix[positive_time, :]

        finite_signal_mask = np.any(np.isfinite(signal_matrix), axis=0)
        if not np.any(finite_signal_mask):
            message = "Cannot repair: no valid signal column was detected." if english else "无法修复：没有有效信号列。"
            return AgentToolResult("failed", message, error="no_valid_signal")

        signal_matrix = signal_matrix[:, finite_signal_mask]
        data = {"time_ms": time_values}
        signal_columns = [layout["signal_columns"][idx] for idx, keep in enumerate(finite_signal_mask) if keep]
        for idx, signal_col in enumerate(signal_columns):
            data[str(signal_col["label"])] = signal_matrix[:, idx]

        output_path = Path(output_dir) / f"{safe_token(Path(input_workbook).stem)}__standardized.xlsx"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(data).to_excel(output_path, index=False)
        message = "Standardized Excel generated: the first column is time_ms, followed by valid signal columns." if english else "已生成标准化 Excel：第一列为 time_ms，后续列为有效信号。"
        return AgentToolResult(
            "success",
            message,
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
        message = "Excel auto-repair failed." if _is_english(language) else "Excel 自动修复失败。"
        return AgentToolResult("failed", message, error=str(exc))


def run_lcurve(input_workbook: Path, output_dir: Path, params: dict[str, Any] | None = None, language: str = "中文") -> AgentToolResult:
    """Run L-curve inversion and return exported artifacts."""

    params = params or {}
    try:
        english = _is_english(language)
        if _workbook_data_kind(Path(input_workbook)) == "spectrum":
            return _spectrum_input_error(language)
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
        message = "L-curve inversion completed. The smoothing factor was selected automatically, and the T2 spectrum, metrics table, and figures were exported." if english else "L-curve 反演完成，已自动选择平滑因子并导出 T2 谱、指标表和图像。"
        return AgentToolResult(
            "success",
            message,
            artifacts=artifacts,
            summary=summary,
        )
    except Exception as exc:
        message = "L-curve inversion failed." if _is_english(language) else "L-curve 反演失败。"
        return AgentToolResult("failed", message, error=str(exc))


def run_fixed_nnls(input_workbook: Path, output_dir: Path, params: dict[str, Any] | None = None, language: str = "中文") -> AgentToolResult:
    """Run fixed-regularization NNLS inversion."""

    params = params or {}
    try:
        english = _is_english(language)
        if _workbook_data_kind(Path(input_workbook)) == "spectrum":
            return _spectrum_input_error(language)
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
        message = f"Fixed-regularization NNLS inversion completed with smoothing factor {regularization:g}." if english else f"固定 NNLS 反演完成，使用平滑因子 {regularization:g}。"
        return AgentToolResult(
            "success",
            message,
            artifacts=artifacts,
            summary=summary,
        )
    except Exception as exc:
        message = "Fixed-regularization NNLS inversion failed." if _is_english(language) else "固定 NNLS 反演失败。"
        return AgentToolResult("failed", message, error=str(exc))


def plot_decay_spectrum(
    raw_decay_workbook: Path,
    spectrum_workbook: Path,
    output_dir: Path,
    params: dict[str, Any] | None = None,
    language: str = "中文",
) -> AgentToolResult:
    """Generate paired decay/T2 spectrum plots."""

    params = params or {}
    try:
        english = _is_english(language)
        result = run_plotting_workbook_pair(
            Path(raw_decay_workbook),
            Path(spectrum_workbook),
            Path(output_dir),
            plot_config=PlotConfig(),
            time_to_ms_scale=float(params.get("time_to_ms_scale", 1.0)),
        )
        message = "Paired decay-curve and T2-spectrum figures were generated." if english else "衰减曲线和 T2 谱配对图已生成。"
        return AgentToolResult(
            "success",
            message,
            artifacts=_as_artifacts(list(result.values())),
            summary={"figure_count": len(result)},
        )
    except Exception as exc:
        message = "Paired figure generation failed." if _is_english(language) else "配对图生成失败。"
        return AgentToolResult("failed", message, error=str(exc))


def run_gaussian_peaks(spectrum_workbook: Path, output_dir: Path, params: dict[str, Any] | None = None, language: str = "中文") -> AgentToolResult:
    """Run Gaussian peak decomposition on a spectrum workbook."""

    params = params or {}
    try:
        english = _is_english(language)
        peak_count = int(params.get("peak_count", 2))
        result = run_gaussian_decomposition_on_spectrum_workbook(
            Path(spectrum_workbook),
            Path(output_dir),
            config=GaussianConfig(peak_count=peak_count),
            plot_config=PlotConfig(),
        )
        message = f"Gaussian peak decomposition completed with {peak_count} peaks." if english else f"Gaussian 分峰完成，使用 {peak_count} 个峰。"
        return AgentToolResult(
            "success",
            message,
            artifacts=_as_artifacts(result),
            summary={key: str(value) for key, value in result.items()} | {"peak_count": peak_count},
        )
    except Exception as exc:
        message = "Gaussian peak decomposition failed." if _is_english(language) else "Gaussian 分峰失败。"
        return AgentToolResult("failed", message, error=str(exc))


def generate_report(
    output_dir: Path,
    *,
    user_goal: str,
    validation: AgentToolResult,
    workflow_results: list[AgentToolResult],
    parameter_notes: str,
    language: str = "中文",
) -> AgentToolResult:
    """Generate a Markdown report from tool results."""

    try:
        english = _is_english(language)
        output_path = Path(output_dir) / "report.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if english:
            lines = [
                "# T2 Inversion Agent Report",
                "",
                "## User Goal",
                user_goal.strip() or "The user did not provide an additional goal, so the default T2 inversion workflow was used.",
                "",
                "## Data Diagnosis",
                validation.message,
                "",
                "```text",
                str(validation.summary),
                "```",
                "",
                "## Parameter Explanation and Selection",
                parameter_notes,
                "",
                "## Tool Results",
            ]
        else:
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
            if english:
                lines.extend(
                    [
                        f"### Step {idx}",
                        f"- Status: {result.status}",
                        f"- Description: {result.message}",
                        f"- Output count: {len(result.artifacts)}",
                    ]
                )
            else:
                lines.extend(
                    [
                        f"### 步骤 {idx}",
                        f"- 状态：{result.status}",
                        f"- 说明：{result.message}",
                        f"- 输出数量：{len(result.artifacts)}",
                    ]
                )
            if result.error:
                lines.append(f"- Error: {result.error}" if english else f"- 错误：{result.error}")
            if result.summary:
                lines.extend(["", "```text", str(result.summary), "```"])
            lines.append("")

        if english:
            lines.extend(
                [
                    "## Notes",
                    "- Smaller smoothing factors fit noise more easily; larger values can smooth away real small peaks.",
                    "- L-curve is suitable for first-pass analysis, but final interpretation should still use sample background and experimental conditions.",
                    "- Gaussian peak decomposition is a spectrum-interpretation tool, not a unique physical component assignment.",
                ]
            )
        else:
            lines.extend(
                [
                    "## 注意事项",
                    "- 平滑因子越小，越容易贴合噪声；越大，越容易抹平真实小峰。",
                    "- L-curve 适合初次分析，但最终解释仍建议结合样品背景和实验条件。",
                    "- Gaussian 分峰是谱形解释工具，不等同于唯一的物理组分划分。",
                ]
            )

        output_path.write_text("\n".join(lines), encoding="utf-8")
        message = "English Markdown report generated." if english else "中文 Markdown 报告已生成。"
        return AgentToolResult("success", message, artifacts=[str(output_path)], summary={"report": str(output_path)})
    except Exception as exc:
        message = "Report generation failed." if _is_english(language) else "报告生成失败。"
        return AgentToolResult("failed", message, error=str(exc))
