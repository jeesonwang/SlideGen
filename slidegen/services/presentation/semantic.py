from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from slidegen.services.document.markdown import Heading
from slidegen.services.document.markdown.elements import Element, Table


class SlideKind(str, Enum):
    CONTENT_POINTS = "content_points"
    DATA_TABLE = "data_table"


class BlockKind(str, Enum):
    POINT = "point"
    PARAGRAPH = "paragraph"
    TABLE = "table"


@dataclass(frozen=True)
class BlockSpec:
    kind: BlockKind
    title: str
    text: str


@dataclass(frozen=True)
class SlideSpec:
    kind: SlideKind
    title: str
    source_level: int
    blocks: tuple[BlockSpec, ...]


def build_content_slide_spec(content: Heading) -> SlideSpec:
    blocks: list[BlockSpec] = []
    for child in content.children:
        if isinstance(child, Heading):
            blocks.append(BlockSpec(kind=BlockKind.POINT, title=child.element_text, text=child.text.strip()))
        elif isinstance(child, Table):
            blocks.append(BlockSpec(kind=BlockKind.TABLE, title=", ".join(child.headers), text=child.element_text_source))
        elif isinstance(child, Element) and child.element_text.strip():
            blocks.append(BlockSpec(kind=BlockKind.PARAGRAPH, title="", text=child.element_text.strip()))

    slide_kind = SlideKind.DATA_TABLE if any(block.kind is BlockKind.TABLE for block in blocks) else SlideKind.CONTENT_POINTS
    return SlideSpec(kind=slide_kind, title=content.element_text, source_level=content.level, blocks=tuple(blocks))
