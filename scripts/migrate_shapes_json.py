from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SUPPORTED_SHAPES = {"rect", "rectangle", "roundRect", "rounded_rect"}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_location(shape: dict[str, Any]) -> dict[str, float] | None:
    loc = shape.get("location") or shape.get("bbox") or shape.get("position")
    if not isinstance(loc, dict):
        return None
    x = _as_float(loc.get("x") or loc.get("left"))
    y = _as_float(loc.get("y") or loc.get("top"))
    w = _as_float(loc.get("w") or loc.get("width"))
    h = _as_float(loc.get("h") or loc.get("height"))
    if w <= 0 or h <= 0:
        return None
    return {"x": x, "y": y, "w": w, "h": h}


def migrate_shapes(shapes: list[dict[str, Any]], slide_w: float, slide_h: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    regions: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for idx, shape in enumerate(shapes):
        shape_type = str(shape.get("shape_type") or shape.get("type") or "").strip()
        loc = _extract_location(shape)
        fill = shape.get("fill") or shape.get("fill_color")
        line = shape.get("line") or shape.get("line_color")
        if shape_type not in SUPPORTED_SHAPES or loc is None or not (fill or line):
            skipped.append({"index": idx, "reason": "unsupported_shape_or_missing_style", "shape_type": shape_type})
            continue
        regions.append(
            {
                "region_id": f"migrated_deco_{idx}",
                "role": "decoration",
                "x_frac": round(loc["x"] / slide_w, 4),
                "y_frac": round(loc["y"] / slide_h, 4),
                "w_frac": round(loc["w"] / slide_w, 4),
                "h_frac": round(loc["h"] / slide_h, 4),
                "decoration_shape": "rounded_rect" if shape_type in {"roundRect", "rounded_rect"} else "rect",
                "fill": fill,
                "line": line,
            }
        )
    return regions, skipped


def migrate_file(shapes_json: Path, output_report: Path, slide_w: float, slide_h: float) -> dict[str, Any]:
    payload = json.loads(shapes_json.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        shapes = payload
    elif isinstance(payload, dict):
        shapes = payload.get("shapes", [])
    else:
        shapes = []
    if not isinstance(shapes, list):
        raise ValueError("shapes.json must contain a list or a top-level 'shapes' list")
    regions, skipped = migrate_shapes(shapes, slide_w=slide_w, slide_h=slide_h)
    report = {"input": str(shapes_json), "converted": regions, "skipped": skipped}
    output_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate stable shapes.json decoration styles into recipe DECORATION regions.")
    parser.add_argument("shapes_json", type=Path)
    parser.add_argument("--output-report", type=Path, default=Path("migration_report.json"))
    parser.add_argument("--slide-width", type=float, default=13.333)
    parser.add_argument("--slide-height", type=float, default=7.5)
    args = parser.parse_args()
    report = migrate_file(args.shapes_json, args.output_report, args.slide_width, args.slide_height)
    print(f"converted={len(report['converted'])} skipped={len(report['skipped'])} report={args.output_report}")


if __name__ == "__main__":
    main()
