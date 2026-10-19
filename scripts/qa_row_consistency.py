#!/usr/bin/env python3
"""Flag palette, exposure, and scale drift across a Codex v2 pet atlas."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

from PIL import Image


USED_COLUMNS = (6, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8)


def median(values: list[float]) -> float:
    return round(float(statistics.median(values)), 3)


def cell_stats(cell: Image.Image) -> dict[str, float | list[int] | None]:
    pixels = [(r, g, b, a) for r, g, b, a in cell.getdata() if a > 16]
    if not pixels:
        return {"empty": True, "bbox": None, "area": 0}
    alpha = cell.getchannel("A")
    bbox = alpha.point(lambda value: 255 if value > 16 else 0).getbbox()
    assert bbox is not None
    r = sum(pixel[0] for pixel in pixels) / len(pixels)
    g = sum(pixel[1] for pixel in pixels) / len(pixels)
    b = sum(pixel[2] for pixel in pixels) / len(pixels)
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return {
        "empty": False,
        "bbox": list(bbox),
        "width": bbox[2] - bbox[0],
        "height": bbox[3] - bbox[1],
        "area": len(pixels),
        "mean_rgb": [round(r, 3), round(g, 3), round(b, 3)],
        "luminance": round(luminance, 3),
    }


def row_summary(cells: list[dict]) -> dict:
    valid = [cell for cell in cells if not cell["empty"]]
    return {
        "frames": len(valid),
        "median_width": median([float(cell["width"]) for cell in valid]) if valid else 0,
        "median_height": median([float(cell["height"]) for cell in valid]) if valid else 0,
        "median_area": median([float(cell["area"]) for cell in valid]) if valid else 0,
        "mean_rgb": [median([float(cell["mean_rgb"][channel]) for cell in valid]) for channel in range(3)] if valid else [0, 0, 0],
        "median_luminance": median([float(cell["luminance"]) for cell in valid]) if valid else 0,
        "luminance_spread": round(max(float(cell["luminance"]) for cell in valid) - min(float(cell["luminance"]) for cell in valid), 3) if valid else 0,
    }


def rgb_distance(left: list[float], right: list[float]) -> float:
    return round(math.sqrt(sum((left[index] - right[index]) ** 2 for index in range(3))), 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas", required=True, type=Path)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    atlas_path = args.atlas.expanduser().resolve()
    with Image.open(atlas_path) as opened:
        atlas = opened.convert("RGBA")
    if atlas.size != (1536, 2288):
        raise SystemExit(f"Expected 1536x2288 v2 atlas, got {atlas.width}x{atlas.height}")

    rows: list[dict] = []
    errors: list[str] = []
    warnings: list[str] = []
    for row_index, used in enumerate(USED_COLUMNS):
        cells = []
        for column in range(used):
            cell = atlas.crop((column * 192, row_index * 208, (column + 1) * 192, (row_index + 1) * 208))
            stats = cell_stats(cell)
            stats["column"] = column
            cells.append(stats)
            if stats["empty"]:
                errors.append(f"row {row_index} column {column} is empty")
        summary = row_summary(cells)
        rows.append({"row": row_index, "used_columns": used, "summary": summary, "cells": cells})
        if summary["luminance_spread"] > 24:
            warnings.append(f"row {row_index} has high within-row luminance spread: {summary['luminance_spread']}")

    idle = rows[0]["summary"]
    look_a = rows[9]["summary"]
    look_b = rows[10]["summary"]
    paired_height_ratio = round(look_b["median_height"] / look_a["median_height"], 3) if look_a["median_height"] else 0
    paired_luminance_delta = round(abs(look_b["median_luminance"] - look_a["median_luminance"]), 3)
    paired_rgb_distance = rgb_distance(look_a["mean_rgb"], look_b["mean_rgb"])

    if not 0.88 <= paired_height_ratio <= 1.12:
        errors.append(f"look rows median-height ratio is {paired_height_ratio}; expected 0.88-1.12")
    if paired_luminance_delta > 14:
        errors.append(f"look rows luminance delta is {paired_luminance_delta}; expected <=14")
    if paired_rgb_distance > 18:
        errors.append(f"look rows RGB distance is {paired_rgb_distance}; expected <=18")

    idle_comparisons = {}
    for row_index in (9, 10):
        summary = rows[row_index]["summary"]
        luminance_delta = round(abs(summary["median_luminance"] - idle["median_luminance"]), 3)
        color_distance = rgb_distance(summary["mean_rgb"], idle["mean_rgb"])
        idle_comparisons[str(row_index)] = {"luminance_delta": luminance_delta, "rgb_distance": color_distance}
        if luminance_delta > 12:
            warnings.append(f"row {row_index} differs from idle luminance by {luminance_delta}")
        if color_distance > 15:
            warnings.append(f"row {row_index} differs from idle RGB by {color_distance}")

    report = {
        "ok": not errors,
        "atlas": str(atlas_path),
        "contract": {"size": [1536, 2288], "cell": [192, 208], "rows": 11},
        "paired_look_rows": {
            "median_height_ratio_row10_to_row9": paired_height_ratio,
            "luminance_delta": paired_luminance_delta,
            "rgb_distance": paired_rgb_distance,
        },
        "idle_comparisons": idle_comparisons,
        "errors": errors,
        "warnings": warnings,
        "rows": rows,
        "note": "Automatic triage only; review warnings against the contact sheet.",
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
