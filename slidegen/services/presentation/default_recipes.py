from __future__ import annotations

from collections.abc import Callable

from slidegen.services.presentation.design_tokens import DesignTokens
from slidegen.services.presentation.recipes import LayoutRecipe
from slidegen.services.presentation.region import Region, RegionRole
from slidegen.services.presentation.semantic import BlockKind

ALL_BLOCK_KINDS = frozenset({BlockKind.POINT, BlockKind.PARAGRAPH, BlockKind.TABLE})


def title_body_recipe(tokens: DesignTokens, n_blocks: int = 1) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    margin_y = tokens.page_margin_y / tokens.slide_height
    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=margin_y, w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
    ]
    if n_blocks <= 0:
        return LayoutRecipe(
            name="TitleBodyRecipe",
            regions=tuple(regions),
            region_roles={"title": RegionRole.TITLE},
            region_text_sources={"title": "slide_title"},
            supported_block_kinds=ALL_BLOCK_KINDS,
        )
    body_top = margin_y + 0.16
    body_h = (1.0 - margin_y - body_top - 0.06) / n_blocks
    region_roles: dict[str, RegionRole] = {"title": RegionRole.TITLE}
    region_block_indexes: dict[str, int] = {}
    region_text_sources: dict[str, str] = {"title": "slide_title"}
    for i in range(n_blocks):
        rid = f"body_{i}"
        regions.append(
            Region(
                region_id=rid,
                x_frac=margin_x,
                y_frac=body_top + i * body_h,
                w_frac=1.0 - 2 * margin_x,
                h_frac=body_h,
                z_layer=10,
            ),
        )
        region_roles[rid] = RegionRole.BODY
        region_block_indexes[rid] = i
        region_text_sources[rid] = "block_text"
    return LayoutRecipe(
        name="TitleBodyRecipe",
        regions=tuple(regions),
        region_roles=region_roles,
        region_block_indexes=region_block_indexes,
        region_text_sources=region_text_sources,
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def grid_cards_recipe(tokens: DesignTokens, n_blocks: int) -> LayoutRecipe:
    if n_blocks <= 0:
        return title_body_recipe(tokens, n_blocks=0)
    margin_x = tokens.page_margin_x / tokens.slide_width
    margin_y = tokens.page_margin_y / tokens.slide_height
    gap_frac = tokens.card_gap / tokens.slide_width

    cols = 3 if n_blocks >= 6 else 2 if n_blocks >= 3 else n_blocks
    rows = (n_blocks + cols - 1) // cols
    card_w = (1.0 - 2 * margin_x - (cols - 1) * gap_frac) / cols
    card_h = (1.0 - 2 * margin_y - 0.18 - (rows - 1) * gap_frac) / rows
    title_y = margin_y
    body_top = title_y + 0.18

    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=title_y, w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
    ]

    card_regions = []
    for i in range(n_blocks):
        col = i % cols
        row = i // cols
        rx = margin_x + col * (card_w + gap_frac)
        ry = body_top + row * (card_h + gap_frac)
        card_id = f"card_{i}"
        card_regions.append(
            Region(
                region_id=card_id,
                x_frac=rx,
                y_frac=ry,
                w_frac=card_w,
                h_frac=card_h,
                z_layer=10,
            )
        )
        regions.append(
            Region(
                region_id=f"{card_id}_icon",
                x_frac=rx + 0.02,
                y_frac=ry + 0.02,
                w_frac=min(0.05, card_w * 0.18),
                h_frac=min(0.08, card_h * 0.28),
                z_layer=11,
            )
        )
        regions.append(
            Region(
                region_id=f"{card_id}_body",
                x_frac=rx + 0.02,
                y_frac=ry + 0.12,
                w_frac=card_w - 0.04,
                h_frac=card_h - 0.14,
                z_layer=11,
            )
        )

    all_recipe_regions = regions + card_regions
    region_roles = {
        r.region_id: RegionRole.TITLE
        if "title" in r.region_id
        else (
            RegionRole.ICON
            if r.region_id.endswith("_icon")
            else RegionRole.CARD
            if r.region_id.startswith("card_") and "_body" not in r.region_id
            else RegionRole.CARD_BODY
        )
        for r in all_recipe_regions
    }
    region_block_indexes = {}
    region_text_sources = {"title": "slide_title"}
    for i in range(n_blocks):
        region_block_indexes[f"card_{i}_icon"] = i
        region_block_indexes[f"card_{i}_body"] = i
        region_text_sources[f"card_{i}_body"] = "block_title_text"

    return LayoutRecipe(
        name="GridCardsRecipe",
        regions=tuple(all_recipe_regions),
        region_roles=region_roles,
        region_block_indexes=region_block_indexes,
        region_text_sources=region_text_sources,
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def two_column_recipe(tokens: DesignTokens, n_blocks: int = 2) -> LayoutRecipe:
    if n_blocks != 2:
        return title_body_recipe(tokens, n_blocks=n_blocks)
    margin_x = tokens.page_margin_x / tokens.slide_width
    margin_y = tokens.page_margin_y / tokens.slide_height
    gap_frac = tokens.card_gap / tokens.slide_width
    col_w = (1.0 - 2 * margin_x - gap_frac) / 2
    col_top = margin_y + 0.16
    col_h = 1.0 - margin_y - col_top - 0.06

    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=margin_y, w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
        Region(region_id="left_col", x_frac=margin_x, y_frac=col_top, w_frac=col_w, h_frac=col_h, z_layer=10),
        Region(
            region_id="right_col",
            x_frac=margin_x + col_w + gap_frac,
            y_frac=col_top,
            w_frac=col_w,
            h_frac=col_h,
            z_layer=10,
        ),
    ]
    return LayoutRecipe(
        name="TwoColumnRecipe",
        regions=tuple(regions),
        region_roles={
            "title": RegionRole.TITLE,
            "left_col": RegionRole.CARD_BODY,
            "right_col": RegionRole.CARD_BODY,
        },
        region_block_indexes={"left_col": 0, "right_col": 1},
        region_text_sources={"title": "slide_title", "left_col": "block_title_text", "right_col": "block_title_text"},
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def cover_recipe(tokens: DesignTokens) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=0.32, w_frac=1.0 - 2 * margin_x, h_frac=0.15, z_layer=10),
        Region(region_id="subtitle", x_frac=margin_x, y_frac=0.50, w_frac=1.0 - 2 * margin_x, h_frac=0.10, z_layer=10),
        Region(
            region_id="deco_bar",
            x_frac=margin_x,
            y_frac=0.70,
            w_frac=0.15,
            h_frac=0.02,
            z_layer=20,
            decoration_shape="rounded_rect",
            fill_role="accent",
        ),
    ]
    return LayoutRecipe(
        name="CoverRecipe",
        regions=tuple(regions),
        region_roles={
            "title": RegionRole.TITLE,
            "subtitle": RegionRole.SUBTITLE,
            "deco_bar": RegionRole.DECORATION,
        },
        region_block_indexes={"subtitle": 0},
        region_text_sources={"title": "slide_title", "subtitle": "block_text"},
        supported_block_kinds=frozenset({BlockKind.TITLE, BlockKind.SUBTITLE}),
    )


def agenda_recipe(tokens: DesignTokens, n_blocks: int) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    margin_y = tokens.page_margin_y / tokens.slide_height
    gap_frac = tokens.card_gap / tokens.slide_width

    available_h = 1.0 - 2 * margin_y - 0.18
    card_h = min(0.35, (available_h - (n_blocks - 1) * gap_frac / 2) / n_blocks)
    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=margin_y, w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
    ]
    card_regions = []
    body_regions = []
    idx_regions = []
    for i in range(min(n_blocks, 8)):
        ry = margin_y + 0.18 + i * (card_h + gap_frac / 2)
        card_id = f"agenda_card_{i}"
        body_id = f"agenda_body_{i}"
        idx_id = f"agenda_index_{i}"
        card_regions.append(
            Region(
                region_id=card_id,
                x_frac=margin_x + 0.06,
                y_frac=ry,
                w_frac=1.0 - 2 * margin_x - 0.06,
                h_frac=card_h,
                z_layer=10,
                decoration_shape="rounded_rect",
                fill_role="light_bg_alt",
            )
        )
        body_regions.append(
            Region(
                region_id=body_id,
                x_frac=margin_x + 0.09,
                y_frac=ry + 0.02,
                w_frac=1.0 - 2 * margin_x - 0.12,
                h_frac=max(card_h - 0.04, 0.01),
                z_layer=11,
            )
        )
        idx_regions.append(
            Region(
                region_id=idx_id,
                x_frac=margin_x,
                y_frac=ry,
                w_frac=0.06,
                h_frac=card_h,
                z_layer=10,
            )
        )

    all_agenda_regions = regions + card_regions + body_regions + idx_regions
    region_roles = {"title": RegionRole.TITLE}
    region_block_indexes = {}
    region_text_sources = {"title": "slide_title"}
    for i in range(min(n_blocks, 8)):
        region_roles[f"agenda_card_{i}"] = RegionRole.CARD
        region_roles[f"agenda_body_{i}"] = RegionRole.CARD_BODY
        region_roles[f"agenda_index_{i}"] = RegionRole.INDEX
        region_block_indexes[f"agenda_body_{i}"] = i
        region_block_indexes[f"agenda_index_{i}"] = i
        region_text_sources[f"agenda_body_{i}"] = "block_title_text"
        region_text_sources[f"agenda_index_{i}"] = "index"

    return LayoutRecipe(
        name="AgendaRecipe",
        regions=tuple(all_agenda_regions),
        region_roles=region_roles,
        region_block_indexes=region_block_indexes,
        region_text_sources=region_text_sources,
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def closing_recipe(tokens: DesignTokens) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    regions = [
        Region(region_id="thanks", x_frac=margin_x, y_frac=0.40, w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
        Region(
            region_id="deco_top",
            x_frac=0.0,
            y_frac=0.0,
            w_frac=1.0,
            h_frac=0.03,
            z_layer=20,
            decoration_shape="rect",
            fill_role="primary",
        ),
        Region(
            region_id="deco_bottom",
            x_frac=0.0,
            y_frac=0.97,
            w_frac=1.0,
            h_frac=0.03,
            z_layer=20,
            decoration_shape="rect",
            fill_role="primary",
        ),
    ]
    return LayoutRecipe(
        name="ClosingRecipe",
        regions=tuple(regions),
        region_roles={
            "thanks": RegionRole.TITLE,
            "deco_top": RegionRole.DECORATION,
            "deco_bottom": RegionRole.DECORATION,
        },
        region_text_sources={"thanks": "slide_title"},
        supported_block_kinds=frozenset({BlockKind.TITLE}),
    )


def section_cover_recipe(tokens: DesignTokens) -> LayoutRecipe:
    """Chapter divider inspired by the old shapes.json chapter-home slides."""
    margin_x = tokens.page_margin_x / tokens.slide_width
    regions = [
        Region(
            region_id="top_bar",
            x_frac=0.0,
            y_frac=0.0,
            w_frac=1.0,
            h_frac=0.08,
            z_layer=1,
            decoration_shape="rect",
            fill_role="primary",
        ),
        Region(
            region_id="accent_block",
            x_frac=margin_x,
            y_frac=0.30,
            w_frac=0.08,
            h_frac=0.22,
            z_layer=2,
            decoration_shape="rounded_rect",
            fill_role="accent",
        ),
        Region(
            region_id="section_title",
            x_frac=margin_x + 0.12,
            y_frac=0.32,
            w_frac=1.0 - 2 * margin_x - 0.12,
            h_frac=0.16,
            z_layer=10,
        ),
        Region(
            region_id="bottom_rule",
            x_frac=margin_x + 0.12,
            y_frac=0.53,
            w_frac=0.48,
            h_frac=0.012,
            z_layer=3,
            decoration_shape="rect",
            fill_role="accent",
        ),
        Region(
            region_id="soft_circle",
            x_frac=0.72,
            y_frac=0.50,
            w_frac=0.22,
            h_frac=0.38,
            z_layer=1,
            decoration_shape="ellipse",
            fill_role="light_bg_alt",
        ),
    ]
    return LayoutRecipe(
        name="SectionCoverRecipe",
        regions=tuple(regions),
        region_roles={
            "top_bar": RegionRole.DECORATION,
            "accent_block": RegionRole.DECORATION,
            "section_title": RegionRole.TITLE,
            "bottom_rule": RegionRole.DECORATION,
            "soft_circle": RegionRole.DECORATION,
        },
        region_text_sources={"section_title": "slide_title"},
        supported_block_kinds=frozenset({BlockKind.TITLE}),
    )


def classic_one_point_recipe(tokens: DesignTokens) -> LayoutRecipe:
    """Code-migrated equivalent of a one-point shapes.json layout."""
    margin_x = tokens.page_margin_x / tokens.slide_width
    margin_y = tokens.page_margin_y / tokens.slide_height
    regions = [
        Region(region_id="slide_title", x_frac=margin_x, y_frac=margin_y, w_frac=0.74, h_frac=0.12, z_layer=10),
        Region(
            region_id="accent_pill",
            x_frac=margin_x,
            y_frac=0.32,
            w_frac=0.19,
            h_frac=0.07,
            z_layer=2,
            decoration_shape="rounded_rect",
            fill_role="accent",
        ),
        Region(region_id="point_title_0", x_frac=margin_x + 0.025, y_frac=0.325, w_frac=0.15, h_frac=0.06, z_layer=10),
        Region(
            region_id="content_panel",
            x_frac=margin_x,
            y_frac=0.42,
            w_frac=0.78,
            h_frac=0.38,
            z_layer=1,
            decoration_shape="rounded_rect",
            fill_role="light_bg",
        ),
        Region(region_id="point_body_0", x_frac=margin_x + 0.04, y_frac=0.47, w_frac=0.70, h_frac=0.26, z_layer=10),
        Region(
            region_id="soft_circle",
            x_frac=0.70,
            y_frac=0.30,
            w_frac=0.22,
            h_frac=0.38,
            z_layer=0,
            decoration_shape="ellipse",
            fill_role="light_bg_alt",
        ),
    ]
    return LayoutRecipe(
        name="ClassicOnePointRecipe",
        regions=tuple(regions),
        region_roles={
            "slide_title": RegionRole.TITLE,
            "accent_pill": RegionRole.DECORATION,
            "point_title_0": RegionRole.CARD_BODY,
            "content_panel": RegionRole.DECORATION,
            "point_body_0": RegionRole.BODY,
            "soft_circle": RegionRole.DECORATION,
        },
        region_block_indexes={"point_title_0": 0, "point_body_0": 0},
        region_text_sources={
            "slide_title": "slide_title",
            "point_title_0": "block_title",
            "point_body_0": "block_text",
        },
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def classic_two_points_recipe(_tokens: DesignTokens) -> LayoutRecipe:
    return _classic_numbered_stack_recipe(
        "ClassicTwoPointsRecipe",
        n_blocks=2,
        y_positions=(0.22, 0.55),
        card_h=0.24,
    )


def classic_three_points_recipe(_tokens: DesignTokens) -> LayoutRecipe:
    return _classic_cards_recipe("ClassicThreePointsRecipe", n_blocks=3, cols=2)


def classic_four_points_recipe(_tokens: DesignTokens) -> LayoutRecipe:
    return _classic_cards_recipe("ClassicFourPointsRecipe", n_blocks=4, cols=2)


def _classic_numbered_stack_recipe(
    name: str, *, n_blocks: int, y_positions: tuple[float, ...], card_h: float
) -> LayoutRecipe:
    margin_x = 0.075
    regions = [
        Region(region_id="slide_title", x_frac=margin_x, y_frac=0.08, w_frac=0.82, h_frac=0.10, z_layer=10),
    ]
    region_roles: dict[str, RegionRole] = {"slide_title": RegionRole.TITLE}
    region_block_indexes: dict[str, int] = {}
    region_text_sources: dict[str, str] = {"slide_title": "slide_title"}

    for i in range(n_blocks):
        y = y_positions[i]
        regions.extend(
            [
                Region(
                    region_id=f"item_card_{i}",
                    x_frac=margin_x + 0.12,
                    y_frac=y,
                    w_frac=0.74,
                    h_frac=card_h,
                    z_layer=1,
                    decoration_shape="rounded_rect",
                    fill_role="light_bg",
                ),
                Region(
                    region_id=f"item_index_bg_{i}",
                    x_frac=margin_x,
                    y_frac=y + 0.01,
                    w_frac=0.065,
                    h_frac=0.11,
                    z_layer=2,
                    decoration_shape="rect",
                    fill_role="accent",
                ),
                Region(
                    region_id=f"item_index_{i}",
                    x_frac=margin_x,
                    y_frac=y + 0.025,
                    w_frac=0.065,
                    h_frac=0.07,
                    z_layer=10,
                ),
                Region(
                    region_id=f"item_body_{i}",
                    x_frac=margin_x + 0.16,
                    y_frac=y + 0.045,
                    w_frac=0.66,
                    h_frac=max(card_h - 0.08, 0.04),
                    z_layer=10,
                ),
            ]
        )
        region_roles[f"item_card_{i}"] = RegionRole.DECORATION
        region_roles[f"item_index_bg_{i}"] = RegionRole.DECORATION
        region_roles[f"item_index_{i}"] = RegionRole.INDEX
        region_roles[f"item_body_{i}"] = RegionRole.CARD_BODY
        region_block_indexes[f"item_index_{i}"] = i
        region_block_indexes[f"item_body_{i}"] = i
        region_text_sources[f"item_index_{i}"] = "index"
        region_text_sources[f"item_body_{i}"] = "block_title_text"

    return LayoutRecipe(
        name=name,
        regions=tuple(regions),
        region_roles=region_roles,
        region_block_indexes=region_block_indexes,
        region_text_sources=region_text_sources,
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def _classic_cards_recipe(name: str, *, n_blocks: int, cols: int) -> LayoutRecipe:
    margin_x = 0.075
    margin_y = 0.08
    gap_x = 0.035
    gap_y = 0.035
    title_h = 0.10
    body_top = 0.25
    rows = (n_blocks + cols - 1) // cols
    card_w = (1.0 - 2 * margin_x - (cols - 1) * gap_x) / cols
    card_h = (1.0 - body_top - margin_y - (rows - 1) * gap_y) / rows
    regions = [
        Region(region_id="slide_title", x_frac=margin_x, y_frac=margin_y, w_frac=0.82, h_frac=title_h, z_layer=10),
        Region(
            region_id="title_rule",
            x_frac=margin_x,
            y_frac=margin_y + title_h + 0.025,
            w_frac=0.16,
            h_frac=0.012,
            z_layer=2,
            decoration_shape="rect",
            fill_role="accent",
        ),
    ]
    region_roles: dict[str, RegionRole] = {
        "slide_title": RegionRole.TITLE,
        "title_rule": RegionRole.DECORATION,
    }
    region_block_indexes: dict[str, int] = {}
    region_text_sources: dict[str, str] = {"slide_title": "slide_title"}

    for i in range(n_blocks):
        row = i // cols
        col = i % cols
        x = margin_x + col * (card_w + gap_x)
        y = body_top + row * (card_h + gap_y)
        regions.extend(
            [
                Region(
                    region_id=f"card_{i}",
                    x_frac=x,
                    y_frac=y,
                    w_frac=card_w,
                    h_frac=card_h,
                    z_layer=1,
                    decoration_shape="rounded_rect",
                    fill_role="light_bg",
                ),
                Region(
                    region_id=f"card_accent_{i}",
                    x_frac=x,
                    y_frac=y,
                    w_frac=card_w,
                    h_frac=0.045,
                    z_layer=2,
                    decoration_shape="rect",
                    fill_role="accent",
                ),
                Region(
                    region_id=f"card_index_{i}",
                    x_frac=x + 0.02,
                    y_frac=y + 0.06,
                    w_frac=0.07,
                    h_frac=0.07,
                    z_layer=10,
                ),
                Region(
                    region_id=f"card_body_{i}",
                    x_frac=x + 0.10,
                    y_frac=y + 0.06,
                    w_frac=card_w - 0.13,
                    h_frac=card_h - 0.10,
                    z_layer=10,
                ),
            ]
        )
        region_roles[f"card_{i}"] = RegionRole.CARD
        region_roles[f"card_accent_{i}"] = RegionRole.DECORATION
        region_roles[f"card_index_{i}"] = RegionRole.INDEX
        region_roles[f"card_body_{i}"] = RegionRole.CARD_BODY
        region_block_indexes[f"card_index_{i}"] = i
        region_block_indexes[f"card_body_{i}"] = i
        region_text_sources[f"card_index_{i}"] = "index"
        region_text_sources[f"card_body_{i}"] = "block_title_text"

    return LayoutRecipe(
        name=name,
        regions=tuple(regions),
        region_roles=region_roles,
        region_block_indexes=region_block_indexes,
        region_text_sources=region_text_sources,
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


RECIPE_FACTORIES: dict[str, Callable[..., LayoutRecipe]] = {
    "TitleBodyRecipe": title_body_recipe,
    "GridCardsRecipe": grid_cards_recipe,
    "TwoColumnRecipe": two_column_recipe,
    "CoverRecipe": cover_recipe,
    "AgendaRecipe": agenda_recipe,
    "ClosingRecipe": closing_recipe,
    "SectionCoverRecipe": section_cover_recipe,
    "ClassicOnePointRecipe": classic_one_point_recipe,
    "ClassicTwoPointsRecipe": classic_two_points_recipe,
    "ClassicThreePointsRecipe": classic_three_points_recipe,
    "ClassicFourPointsRecipe": classic_four_points_recipe,
}
