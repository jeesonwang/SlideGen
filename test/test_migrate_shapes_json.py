import json

from scripts.migrate_shapes_json import migrate_file, migrate_shapes


def test_migrate_supported_rect_to_decoration_region():
    regions, skipped = migrate_shapes(
        [
            {
                "shape_type": "rect",
                "location": {"x": 1.0, "y": 1.5, "w": 2.0, "h": 1.0},
                "fill_color": "#112233",
            }
        ],
        slide_w=10.0,
        slide_h=5.0,
    )

    assert skipped == []
    assert regions == [
        {
            "region_id": "migrated_deco_0",
            "role": "decoration",
            "x_frac": 0.1,
            "y_frac": 0.3,
            "w_frac": 0.2,
            "h_frac": 0.2,
            "decoration_shape": "rect",
            "fill": "#112233",
            "line": None,
        }
    ]


def test_skips_complex_or_unstyled_shapes():
    regions, skipped = migrate_shapes(
        [{"shape_type": "freeform", "location": {"x": 0, "y": 0, "w": 1, "h": 1}}],
        slide_w=10.0,
        slide_h=5.0,
    )

    assert regions == []
    assert skipped == [{"index": 0, "reason": "unsupported_shape_or_missing_style", "shape_type": "freeform"}]


def test_migrate_file_writes_report(tmp_path):
    shapes_json = tmp_path / "shapes.json"
    report_path = tmp_path / "migration_report.json"
    shapes_json.write_text(json.dumps({"shapes": [{"shape_type": "rect", "location": {"x": 0, "y": 0, "w": 1, "h": 1}, "line_color": "#000000"}]}), encoding="utf-8")

    report = migrate_file(shapes_json, report_path, slide_w=10.0, slide_h=5.0)

    assert report_path.exists()
    assert len(report["converted"]) == 1
    assert json.loads(report_path.read_text(encoding="utf-8"))["converted"][0]["line"] == "#000000"
