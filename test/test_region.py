import pytest

from slidegen.services.presentation.region import Region, RegionRole, RepeatRule


class TestRegion:
    def test_to_absolute_converts_fraction_to_inches(self):
        r = Region(region_id="test", x_frac=0.5, y_frac=0.25, w_frac=0.8, h_frac=0.1)
        left, top, width, height = r.to_absolute(13.333, 7.5)
        assert left == 6.67
        assert top == 1.88
        assert width == 10.67
        assert height == 0.75

    def test_to_absolute_rounds_to_2_decimals(self):
        r = Region(region_id="test", x_frac=0.333, y_frac=0.111, w_frac=0.456, h_frac=0.789)
        left, top, width, height = r.to_absolute(10.0, 8.0)
        assert left == 3.33
        assert top == 0.89
        assert width == 4.56
        assert height == 6.31

    def test_decoration_fields_default_none_for_content_region(self):
        r = Region(region_id="title", x_frac=0.1, y_frac=0.05, w_frac=0.8, h_frac=0.1)
        assert r.decoration_shape is None
        assert r.fill_role is None
        assert r.line_role is None

    def test_decoration_fields_set_for_decoration_region(self):
        r = Region(
            region_id="deco_bar",
            x_frac=0.0, y_frac=0.0, w_frac=1.0, h_frac=0.02,
            z_layer=20,
            decoration_shape="rect",
            fill_role="primary",
            line_role=None,
        )
        assert r.decoration_shape == "rect"
        assert r.fill_role == "primary"
        assert r.line_role is None


class TestRepeatRule:
    def test_expand_zero_items_returns_empty(self):
        seed = Region(region_id="card", x_frac=0.1, y_frac=0.3, w_frac=0.35, h_frac=0.4)
        rule = RepeatRule(seed=seed, step_x=0.0, step_y=0.12)
        result = rule.expand(0)
        assert len(result) == 0

    def test_expand_single_item_equals_seed(self):
        seed = Region(region_id="card", x_frac=0.1, y_frac=0.3, w_frac=0.35, h_frac=0.4)
        rule = RepeatRule(seed=seed, step_x=0.0, step_y=0.12)
        result = rule.expand(1)
        assert len(result) == 1
        assert result[0].x_frac == seed.x_frac
        assert result[0].y_frac == seed.y_frac

    def test_expand_vertical_stack(self):
        seed = Region(region_id="card", x_frac=0.08, y_frac=0.22, w_frac=0.30, h_frac=0.10)
        rule = RepeatRule(seed=seed, step_x=0.0, step_y=0.13)
        result = rule.expand(3)
        assert len(result) == 3
        assert result[0].region_id == "card_0"
        assert result[1].region_id == "card_1"
        assert result[2].region_id == "card_2"
        assert result[0].y_frac == 0.22
        assert result[1].y_frac == 0.35
        assert result[2].y_frac == 0.48
        for r in result:
            assert r.x_frac == 0.08

    def test_expand_horizontal_row(self):
        seed = Region(region_id="card", x_frac=0.08, y_frac=0.22, w_frac=0.25, h_frac=0.35)
        rule = RepeatRule(seed=seed, step_x=0.30, step_y=0.0)
        result = rule.expand(3)
        assert len(result) == 3
        assert result[0].x_frac == 0.08
        assert result[1].x_frac == 0.38
        assert result[2].x_frac == pytest.approx(0.68)
        for r in result:
            assert r.y_frac == 0.22

    def test_expand_preserves_decoration_fields(self):
        seed = Region(
            region_id="step",
            x_frac=0.08, y_frac=0.22, w_frac=0.30, h_frac=0.10,
            decoration_shape="rounded_rect", fill_role="accent", line_role="primary",
        )
        rule = RepeatRule(seed=seed, step_x=0.05, step_y=0.12, role=RegionRole.CARD)
        result = rule.expand(2)
        for r in result:
            assert r.decoration_shape == "rounded_rect"
            assert r.fill_role == "accent"
            assert r.line_role == "primary"

    def test_expand_staircase_layout(self):
        seed = Region(region_id="agenda_item", x_frac=0.08, y_frac=0.22, w_frac=0.30, h_frac=0.10)
        rule = RepeatRule(seed=seed, step_x=0.05, step_y=0.13)
        result = rule.expand(5)
        assert result[4].x_frac == 0.28  # 0.08 + 0.05*4
        assert result[4].y_frac == 0.74  # 0.22 + 0.13*4
