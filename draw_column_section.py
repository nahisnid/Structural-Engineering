#!/usr/bin/env python3
"""Draw an RC column cross-section with rebars and ties from Excel input."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import pandas as pd


REQUIRED_KEYS = {
    "width_mm",
    "height_mm",
    "cover_mm",
    "bar_dia_mm",
    "tie_dia_mm",
    "n_bars_x",
    "n_bars_y",
}


class InputError(ValueError):
    """Raised when the input workbook is missing or has invalid data."""


def _as_float(name: str, value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"'{name}' must be a number. Got: {value!r}") from exc


def _as_int(name: str, value: object) -> int:
    v = _as_float(name, value)
    if not v.is_integer():
        raise InputError(f"'{name}' must be an integer. Got: {value!r}")
    return int(v)


def read_input_from_excel(excel_path: Path, sheet_name: str = "Section") -> dict[str, object]:
    """Read inputs from Excel.

    Supports two table styles:
      1. key/value table with columns: parameter | value
      2. single-row table where column names are the parameter keys
    """
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
    except ValueError:
        available = pd.ExcelFile(excel_path).sheet_names
        raise InputError(
            f"Sheet '{sheet_name}' not found. Available sheets: {', '.join(available)}"
        )

    if df.empty:
        raise InputError("Input sheet is empty.")

    normalized_cols = [str(c).strip().lower() for c in df.columns]
    if {"parameter", "value"}.issubset(set(normalized_cols)):
        param_col = normalized_cols.index("parameter")
        value_col = normalized_cols.index("value")
        values: dict[str, object] = {}
        for _, row in df.iterrows():
            key = str(row.iloc[param_col]).strip()
            if not key or key.lower() == "nan":
                continue
            values[key] = row.iloc[value_col]
    else:
        values = {str(col).strip(): df.iloc[0, i] for i, col in enumerate(df.columns)}

    missing = REQUIRED_KEYS.difference(values)
    if missing:
        missing_txt = ", ".join(sorted(missing))
        raise InputError(f"Missing required input keys: {missing_txt}")

    parsed = {
        "width_mm": _as_float("width_mm", values["width_mm"]),
        "height_mm": _as_float("height_mm", values["height_mm"]),
        "cover_mm": _as_float("cover_mm", values["cover_mm"]),
        "bar_dia_mm": _as_float("bar_dia_mm", values["bar_dia_mm"]),
        "tie_dia_mm": _as_float("tie_dia_mm", values["tie_dia_mm"]),
        "n_bars_x": _as_int("n_bars_x", values["n_bars_x"]),
        "n_bars_y": _as_int("n_bars_y", values["n_bars_y"]),
        "output_file": values.get("output_file", "column_section.png"),
    }

    if parsed["n_bars_x"] < 2 or parsed["n_bars_y"] < 2:
        raise InputError("'n_bars_x' and 'n_bars_y' must each be at least 2.")

    return parsed


def compute_rebar_positions(
    width_mm: float,
    height_mm: float,
    cover_mm: float,
    tie_dia_mm: float,
    bar_dia_mm: float,
    n_bars_x: int,
    n_bars_y: int,
) -> list[tuple[float, float]]:
    """Compute rebar center coordinates along the perimeter."""
    clear_offset = cover_mm + tie_dia_mm + (bar_dia_mm / 2)

    x_left = clear_offset
    x_right = width_mm - clear_offset
    y_bottom = clear_offset
    y_top = height_mm - clear_offset

    if x_left >= x_right or y_bottom >= y_top:
        raise InputError("Cover/tie/bar settings leave no room for bar placement.")

    xs = [x_left + i * (x_right - x_left) / (n_bars_x - 1) for i in range(n_bars_x)]
    ys = [y_bottom + i * (y_top - y_bottom) / (n_bars_y - 1) for i in range(n_bars_y)]

    points = set()
    for x in xs:
        points.add((round(x, 6), round(y_bottom, 6)))
        points.add((round(x, 6), round(y_top, 6)))
    for y in ys:
        points.add((round(x_left, 6), round(y, 6)))
        points.add((round(x_right, 6), round(y, 6)))

    return sorted(points)


def draw_column_section(data: dict[str, object], output_path: Path) -> None:
    width_mm = float(data["width_mm"])
    height_mm = float(data["height_mm"])
    cover_mm = float(data["cover_mm"])
    bar_dia_mm = float(data["bar_dia_mm"])
    tie_dia_mm = float(data["tie_dia_mm"])
    n_bars_x = int(data["n_bars_x"])
    n_bars_y = int(data["n_bars_y"])

    points = compute_rebar_positions(
        width_mm,
        height_mm,
        cover_mm,
        tie_dia_mm,
        bar_dia_mm,
        n_bars_x,
        n_bars_y,
    )

    fig, ax = plt.subplots(figsize=(8, 8))

    # Concrete outline
    ax.add_patch(Rectangle((0, 0), width_mm, height_mm, fill=False, linewidth=2.2, edgecolor="black"))

    # Tie centerline
    tie_offset = cover_mm + tie_dia_mm / 2
    tie_width = width_mm - 2 * tie_offset
    tie_height = height_mm - 2 * tie_offset
    if tie_width <= 0 or tie_height <= 0:
        raise InputError("Cover and tie diameter leave no room for tie geometry.")

    ax.add_patch(
        Rectangle(
            (tie_offset, tie_offset),
            tie_width,
            tie_height,
            fill=False,
            linewidth=1.8,
            edgecolor="tab:blue",
            linestyle="--",
        )
    )

    # Rebars
    for x, y in points:
        ax.add_patch(
            Circle((x, y), radius=bar_dia_mm / 2, facecolor="tab:red", edgecolor="black", linewidth=0.8)
        )

    bar_count = len(points)

    ax.set_aspect("equal", adjustable="box")
    margin = max(width_mm, height_mm) * 0.15
    ax.set_xlim(-margin, width_mm + margin)
    ax.set_ylim(-margin, height_mm + margin)

    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_title("RC Column Section")
    ax.grid(True, linestyle=":", linewidth=0.6, alpha=0.75)

    note = (
        f"B x H = {width_mm:.0f} x {height_mm:.0f} mm\n"
        f"Bars: {bar_count} - ⌀{bar_dia_mm:.0f} mm\n"
        f"Ties: ⌀{tie_dia_mm:.0f} mm @ cover {cover_mm:.0f} mm"
    )
    ax.text(
        0.02,
        0.98,
        note,
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "gray"},
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Draw an RC column section with rebars and ties from an Excel workbook."
    )
    parser.add_argument("excel_file", type=Path, help="Path to Excel file containing the section inputs")
    parser.add_argument(
        "--sheet",
        default="Section",
        help="Sheet name to read (default: Section)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output image path (overrides output_file in Excel)",
    )
    return parser


def main() -> None:
    parser = build_cli_parser()
    args = parser.parse_args()

    data = read_input_from_excel(args.excel_file, sheet_name=args.sheet)
    output = args.output or Path(str(data["output_file"]))
    draw_column_section(data, output)
    print(f"Column section drawing saved to: {output}")


if __name__ == "__main__":
    main()
