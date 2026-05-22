from __future__ import annotations

import logging

from slidegen.services.presentation.semantic import SlideSpec, SlideKind, BlockKind

logger = logging.getLogger(__name__)


class PresetRecipeFallback:
    """Deterministic fallback when RecipeAgent is unavailable.

    Phase 1a: 返回 recipe name (string)，不依赖 LayoutRecipe 实现。
    Phase 1b: 升级为返回 LayoutRecipe 实例。
    """

    def select_name(self, spec: SlideSpec) -> str:
        """根据 slide_kind + block 数量和密度返回预设 recipe name。

        Returns a recipe name string that Phase 1b factories will resolve.
        """
        n = len(spec.blocks)
        short_blocks = all(b.estimated_text_length < 200 for b in spec.blocks)

        kind = spec.kind

        if kind in (SlideKind.COVER, SlideKind.SECTION_COVER):
            return "CoverRecipe"
        elif kind == SlideKind.AGENDA:
            return "AgendaRecipe"
        elif kind == SlideKind.CLOSING:
            return "ClosingRecipe"
        elif kind == SlideKind.COMPARISON:
            return "TwoColumnRecipe"
        elif kind == SlideKind.CONTENT_POINTS or kind == SlideKind.PROCESS or kind == SlideKind.TIMELINE:
            if n <= 2 and not short_blocks:
                return "TitleBodyRecipe"
            elif n <= 6 and short_blocks:
                return "GridCardsRecipe"
            else:
                return "TitleBodyRecipe"
        elif kind == SlideKind.DATA_TABLE:
            return "TitleBodyRecipe"
        else:
            logger.warning("No preset recipe for slide kind %s, falling back to TitleBodyRecipe", kind)
            return "TitleBodyRecipe"
