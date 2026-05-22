from __future__ import annotations

from slidegen.services.presentation.design_tokens import DesignTokens
from slidegen.services.presentation.recipes import LayoutRecipe
from slidegen.services.presentation.region import Region, RegionRole, RepeatRule
from slidegen.services.presentation.semantic import BlockKind

ALL_BLOCK_KINDS = frozenset({BlockKind.POINT, BlockKind.PARAGRAPH, BlockKind.TABLE})


def title_body_recipe(tokens: DesignTokens, n_blocks: int = 1) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    margin_y = tokens.page_margin_y / tokens.slide_height
    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=margin_y,
               w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
        Region(region_id="body", x_frac=margin_x, y_frac=margin_y + 0.16,
               w_frac=1.0 - 2 * margin_x, h_frac=1.0 - margin_y - 0.22, z_layer=10),
    ]
    return LayoutRecipe(
        name="TitleBodyRecipe",
        regions=tuple(regions),
        region_roles={r.region_id: RegionRole.TITLE if "title" in r.region_id else RegionRole.BODY for r in regions},
        region_block_indexes={"body": 0},
        region_text_sources={"title": "slide_title", "body": "block_text"},
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def grid_cards_recipe(tokens: DesignTokens, n_blocks: int) -> LayoutRecipe:
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
        Region(region_id="title", x_frac=margin_x, y_frac=title_y,
               w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
    ]

    card_regions = []
    for i in range(n_blocks):
        col = i % cols
        row = i // cols
        rx = margin_x + col * (card_w + gap_frac)
        ry = body_top + row * (card_h + gap_frac)
        card_id = f"card_{i}"
        card_regions.append(Region(
            region_id=card_id, x_frac=rx, y_frac=ry,
            w_frac=card_w, h_frac=card_h, z_layer=10,
        ))
        regions.append(Region(
            region_id=f"{card_id}_icon", x_frac=rx + 0.02, y_frac=ry + 0.02,
            w_frac=min(0.05, card_w * 0.18), h_frac=min(0.08, card_h * 0.28), z_layer=11,
        ))
        regions.append(Region(
            region_id=f"{card_id}_body", x_frac=rx + 0.02, y_frac=ry + 0.12,
            w_frac=card_w - 0.04, h_frac=card_h - 0.14, z_layer=11,
        ))

    all_recipe_regions = regions + card_regions
    region_roles = {r.region_id: RegionRole.TITLE if "title" in r.region_id else (
        RegionRole.ICON if r.region_id.endswith("_icon") else
        RegionRole.CARD if r.region_id.startswith("card_") and "_body" not in r.region_id
        else RegionRole.CARD_BODY
    ) for r in all_recipe_regions}
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
    margin_x = tokens.page_margin_x / tokens.slide_width
    margin_y = tokens.page_margin_y / tokens.slide_height
    gap_frac = tokens.card_gap / tokens.slide_width
    col_w = (1.0 - 2 * margin_x - gap_frac) / 2
    col_top = margin_y + 0.16
    col_h = 1.0 - margin_y - col_top - 0.06

    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=margin_y,
               w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
        Region(region_id="left_col", x_frac=margin_x, y_frac=col_top,
               w_frac=col_w, h_frac=col_h, z_layer=10),
        Region(region_id="right_col", x_frac=margin_x + col_w + gap_frac, y_frac=col_top,
               w_frac=col_w, h_frac=col_h, z_layer=10),
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
        Region(region_id="title", x_frac=margin_x, y_frac=0.32,
               w_frac=1.0 - 2 * margin_x, h_frac=0.15, z_layer=10),
        Region(region_id="subtitle", x_frac=margin_x, y_frac=0.50,
               w_frac=1.0 - 2 * margin_x, h_frac=0.10, z_layer=10),
        Region(region_id="deco_bar", x_frac=margin_x, y_frac=0.70,
               w_frac=0.15, h_frac=0.02, z_layer=20,
               decoration_shape="rounded_rect", fill_role="accent"),
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

    card_h = 0.35
    regions = [
        Region(region_id="title", x_frac=margin_x, y_frac=margin_y,
               w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
    ]
    card_regions = []
    idx_regions = []
    for i in range(min(n_blocks, 8)):
        ry = margin_y + 0.18 + i * (card_h + gap_frac / 2)
        card_id = f"agenda_card_{i}"
        idx_id = f"agenda_index_{i}"
        card_regions.append(Region(
            region_id=card_id, x_frac=margin_x + 0.06, y_frac=ry,
            w_frac=1.0 - 2 * margin_x - 0.06, h_frac=card_h, z_layer=10,
        ))
        idx_regions.append(Region(
            region_id=idx_id, x_frac=margin_x, y_frac=ry,
            w_frac=0.06, h_frac=card_h, z_layer=10,
        ))

    all_agenda_regions = regions + card_regions + idx_regions
    region_roles = {r.region_id: RegionRole.TITLE if "title" in r.region_id else (
        RegionRole.INDEX if "index" in r.region_id else RegionRole.CARD
    ) for r in all_agenda_regions}
    region_block_indexes = {}
    region_text_sources = {"title": "slide_title"}
    for i in range(min(n_blocks, 8)):
        region_block_indexes[f"agenda_card_{i}"] = i
        region_block_indexes[f"agenda_index_{i}"] = i
        region_text_sources[f"agenda_card_{i}"] = "block_title_text"
        region_text_sources[f"agenda_index_{i}"] = "index"

    return LayoutRecipe(
        name="AgendaRecipe",
        regions=tuple(regions + card_regions + idx_regions),
        region_roles=region_roles,
        region_block_indexes=region_block_indexes,
        region_text_sources=region_text_sources,
        supported_block_kinds=ALL_BLOCK_KINDS,
    )


def closing_recipe(tokens: DesignTokens) -> LayoutRecipe:
    margin_x = tokens.page_margin_x / tokens.slide_width
    regions = [
        Region(region_id="thanks", x_frac=margin_x, y_frac=0.40,
               w_frac=1.0 - 2 * margin_x, h_frac=0.12, z_layer=10),
        Region(region_id="deco_top", x_frac=0.0, y_frac=0.0,
               w_frac=1.0, h_frac=0.03, z_layer=20,
               decoration_shape="rect", fill_role="primary"),
        Region(region_id="deco_bottom", x_frac=0.0, y_frac=0.97,
               w_frac=1.0, h_frac=0.03, z_layer=20,
               decoration_shape="rect", fill_role="primary"),
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


RECIPE_FACTORIES = {
    "TitleBodyRecipe": title_body_recipe,
    "GridCardsRecipe": grid_cards_recipe,
    "TwoColumnRecipe": two_column_recipe,
    "CoverRecipe": cover_recipe,
    "AgendaRecipe": agenda_recipe,
    "ClosingRecipe": closing_recipe,
}
