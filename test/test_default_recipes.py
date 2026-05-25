from slidegen.services.presentation.default_recipes import (
    RECIPE_FACTORIES,
    agenda_recipe,
    classic_four_points_recipe,
    classic_one_point_recipe,
    classic_three_points_recipe,
    classic_two_points_recipe,
    closing_recipe,
    cover_recipe,
    grid_cards_recipe,
    section_cover_recipe,
    title_body_recipe,
    two_column_recipe,
)
from slidegen.services.presentation.design_tokens import DEFAULT_TOKENS
from slidegen.services.presentation.region import RegionRole


class TestTitleBodyRecipe:
    def test_produces_title_and_body_regions(self):
        recipe = title_body_recipe(DEFAULT_TOKENS)
        assert len(recipe.regions) == 2
        assert "title" in recipe.region_ids
        assert "body_0" in recipe.region_ids

    def test_all_regions_within_canvas(self):
        recipe = title_body_recipe(DEFAULT_TOKENS)
        for region in recipe.regions:
            assert 0.0 <= region.x_frac <= 1.0
            assert 0.0 <= region.y_frac <= 1.0
            assert region.x_frac + region.w_frac <= 1.0 + 0.001
            assert region.y_frac + region.h_frac <= 1.0 + 0.001


class TestGridCardsRecipe:
    def test_4_blocks_produce_2x2_grid(self):
        recipe = grid_cards_recipe(DEFAULT_TOKENS, n_blocks=4)
        card_ids = [rid for rid, role in recipe.region_roles.items() if role == RegionRole.CARD]
        assert len(card_ids) == 4

    def test_card_regions_dont_overlap(self):
        recipe = grid_cards_recipe(DEFAULT_TOKENS, n_blocks=4)
        card_regions = [r for r in recipe.regions if recipe.region_roles.get(r.region_id) == RegionRole.CARD]
        for i, r1 in enumerate(card_regions):
            for j, r2 in enumerate(card_regions):
                if i >= j:
                    continue
                no_overlap = (
                    r1.x_frac + r1.w_frac <= r2.x_frac + 0.001
                    or r2.x_frac + r2.w_frac <= r1.x_frac + 0.001
                    or r1.y_frac + r1.h_frac <= r2.y_frac + 0.001
                    or r2.y_frac + r2.h_frac <= r1.y_frac + 0.001
                )
                assert no_overlap, f"Cards {i} and {j} overlap"


class TestTwoColumnRecipe:
    def test_produces_title_and_two_columns(self):
        recipe = two_column_recipe(DEFAULT_TOKENS)
        assert "title" in recipe.region_ids
        assert "left_col" in recipe.region_ids
        assert "right_col" in recipe.region_ids

    def test_columns_equal_width(self):
        recipe = two_column_recipe(DEFAULT_TOKENS)
        left = next(r for r in recipe.regions if r.region_id == "left_col")
        right = next(r for r in recipe.regions if r.region_id == "right_col")
        assert abs(left.w_frac - right.w_frac) < 0.01


class TestCoverRecipe:
    def test_produces_title_subtitle_decoration(self):
        recipe = cover_recipe(DEFAULT_TOKENS)
        assert "title" in recipe.region_ids
        assert "subtitle" in recipe.region_ids
        assert "deco_bar" in recipe.region_ids

    def test_decoration_has_shape_info(self):
        recipe = cover_recipe(DEFAULT_TOKENS)
        deco = next(r for r in recipe.regions if r.region_id == "deco_bar")
        assert deco.decoration_shape == "rounded_rect"
        assert deco.fill_role == "accent"


class TestAgendaRecipe:
    def test_produces_title_and_cards(self):
        recipe = agenda_recipe(DEFAULT_TOKENS, n_blocks=4)
        card_ids = [rid for rid in recipe.region_ids if "card" in rid]
        assert len(card_ids) == 4

    def test_max_8_blocks(self):
        recipe = agenda_recipe(DEFAULT_TOKENS, n_blocks=10)
        card_ids = [rid for rid in recipe.region_ids if "card" in rid]
        assert len(card_ids) == 8


class TestClosingRecipe:
    def test_produces_thanks_and_decorations(self):
        recipe = closing_recipe(DEFAULT_TOKENS)
        assert "thanks" in recipe.region_ids
        assert "deco_top" in recipe.region_ids
        assert "deco_bottom" in recipe.region_ids


class TestRecipeFactories:
    def test_all_core_recipes_registered(self):
        for name in [
            "TitleBodyRecipe",
            "GridCardsRecipe",
            "TwoColumnRecipe",
            "CoverRecipe",
            "AgendaRecipe",
            "ClosingRecipe",
            "SectionCoverRecipe",
            "ClassicOnePointRecipe",
            "ClassicTwoPointsRecipe",
            "ClassicThreePointsRecipe",
            "ClassicFourPointsRecipe",
        ]:
            assert name in RECIPE_FACTORIES


class TestClassicRecipes:
    def test_one_point_preserves_shape_json_style_roles(self):
        recipe = classic_one_point_recipe(DEFAULT_TOKENS)
        assert recipe.name == "ClassicOnePointRecipe"
        assert "slide_title" in recipe.region_ids
        assert "point_title_0" in recipe.region_ids
        assert "point_body_0" in recipe.region_ids
        assert any(role == RegionRole.DECORATION for role in recipe.region_roles.values())
        assert recipe.region_text_sources["point_title_0"] == "block_title"
        assert recipe.region_text_sources["point_body_0"] == "block_text"

    def test_two_three_four_point_recipes_have_numbered_content_slots(self):
        for factory, expected_count in [
            (classic_two_points_recipe, 2),
            (classic_three_points_recipe, 3),
            (classic_four_points_recipe, 4),
        ]:
            recipe = factory(DEFAULT_TOKENS)
            index_ids = [rid for rid, role in recipe.region_roles.items() if role == RegionRole.INDEX]
            body_ids = [rid for rid, role in recipe.region_roles.items() if role == RegionRole.CARD_BODY]
            assert recipe.name.startswith("Classic")
            assert len(index_ids) == expected_count
            assert len(body_ids) == expected_count

    def test_section_cover_recipe_is_not_generic_title_body(self):
        recipe = section_cover_recipe(DEFAULT_TOKENS)
        assert recipe.name == "SectionCoverRecipe"
        assert "section_title" in recipe.region_ids
        assert any(role == RegionRole.DECORATION for role in recipe.region_roles.values())
        assert recipe.region_text_sources["section_title"] == "slide_title"
