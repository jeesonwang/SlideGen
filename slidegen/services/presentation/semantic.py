from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from slidegen.services.document.markdown import Heading
from slidegen.services.document.markdown.elements import Element, Table


class SlideKind(str, Enum):
    COVER = "cover"
    AGENDA = "agenda"
    SECTION_COVER = "section_cover"
    CONTENT_POINTS = "content_points"
    COMPARISON = "comparison"
    PROCESS = "process"
    TIMELINE = "timeline"
    DATA_TABLE = "data_table"
    DATA_CHART = "data_chart"
    CLOSING = "closing"


class BlockKind(str, Enum):
    TITLE = "title"
    SUBTITLE = "subtitle"
    POINT = "point"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    CHART = "chart"
    IMAGE = "image"
    NOTE = "note"
    SOURCE = "source"


@dataclass(frozen=True)
class BlockSpec:
    kind: BlockKind
    title: str
    text: str
    image_prompt: str | None = None
    icon_query: str | None = None

    @property
    def estimated_text_length(self) -> int:
        return len(self.text)


@dataclass(frozen=True)
class SlideSpec:
    kind: SlideKind
    title: str
    source_level: int
    blocks: tuple[BlockSpec, ...]

    @property
    def total_text_length(self) -> int:
        return sum(block.estimated_text_length for block in self.blocks)

    @property
    def block_kinds(self) -> frozenset[BlockKind]:
        return frozenset(block.kind for block in self.blocks)

    @property
    def has_data(self) -> bool:
        return BlockKind.TABLE in self.block_kinds or BlockKind.CHART in self.block_kinds


_PROCESS_PATTERNS = [
    re.compile(r"^\d+[\.\、\)]", re.MULTILINE),
    re.compile(r"第[一二三四五六七八九十\d]+步"),
]
_TIMELINE_PATTERNS = [
    re.compile(r"\d{4}\s*年"),
    re.compile(r"第[一二三四五六七八九十\d]+\s*(阶段|季度|期)"),
    re.compile(r"Q[1-4]", re.IGNORECASE),
]
_PROCESS_KEYWORDS = frozenset(
    {
        "step",
        "steps",
        "process",
        "procedure",
        "flow",
        "workflow",
        "步骤",
        "流程",
        "过程",
        "阶段",
    }
)


def _has_numbered_list(text: str) -> bool:
    return any(pat.search(text) for pat in _PROCESS_PATTERNS)


def _has_timeline_markers(text: str) -> bool:
    return any(pat.search(text) for pat in _TIMELINE_PATTERNS)


def _has_two_level4_headings(content: Heading) -> bool:
    level4_children = [child for child in content.children if isinstance(child, Heading) and child.level == 4]
    return len(level4_children) == 2


def _has_process_title(content: Heading) -> bool:
    """Check if any child heading's text contains process-related keywords.

    This catches cases where numbered list markers are stripped by the
    markdown parser and cannot be detected via digit patterns.
    """
    for child in content.children:
        if isinstance(child, Heading) and child.element_text.lower() in _PROCESS_KEYWORDS:
            return True
    return False


def infer_slide_kind(content: Heading) -> SlideKind:
    full_text = content.text

    # 显式 hint 优先
    for child in content.children:
        if isinstance(child, Element) and child.element_text.strip().startswith("<!-- slide:"):
            hint = child.element_text.strip()
            if "comparison" in hint:
                return SlideKind.COMPARISON
            elif "process" in hint:
                return SlideKind.PROCESS
            elif "timeline" in hint:
                return SlideKind.TIMELINE
            elif "image_text" in hint:
                return SlideKind.CONTENT_POINTS

    # table 检测 (recursive descendants, since tables nest under child headings)
    if any(isinstance(child, Table) for child in content.descendants):
        return SlideKind.DATA_TABLE

    # 两个 level-4 子标题 → COMPARISON
    if _has_two_level4_headings(content):
        return SlideKind.COMPARISON

    # 子标题包含流程关键词
    if _has_process_title(content):
        return SlideKind.PROCESS

    # 编号列表 → PROCESS
    if _has_numbered_list(full_text):
        return SlideKind.PROCESS

    # 时间线标记 → TIMELINE
    if _has_timeline_markers(full_text):
        return SlideKind.TIMELINE

    return SlideKind.CONTENT_POINTS


def build_content_slide_spec(content: Heading) -> SlideSpec:
    blocks: list[BlockSpec] = []
    seen_ids: set[int] = set()
    for child in content.children:
        seen_ids.add(id(child))
        if isinstance(child, Heading):
            text = child.text.strip()
            icon_query = child.element_text if child.level >= 3 else None
            blocks.append(
                BlockSpec(
                    kind=BlockKind.POINT,
                    title=child.element_text,
                    text=text,
                    icon_query=icon_query,
                )
            )
        elif isinstance(child, Table):
            blocks.append(
                BlockSpec(
                    kind=BlockKind.TABLE,
                    title=", ".join(child.headers),
                    text=child.element_text_source,
                )
            )
        elif isinstance(child, Element) and child.element_text.strip():
            blocks.append(
                BlockSpec(
                    kind=BlockKind.PARAGRAPH,
                    title="",
                    text=child.element_text.strip(),
                )
            )

    # Also collect Table blocks from deeper descendants (infer_slide_kind uses
    # recursive descendants for Table detection, so block collection must match)
    for descendant in content.descendants:
        if isinstance(descendant, Table) and id(descendant) not in seen_ids:
            blocks.append(
                BlockSpec(
                    kind=BlockKind.TABLE,
                    title=", ".join(descendant.headers),
                    text=descendant.element_text_source,
                )
            )

    slide_kind = infer_slide_kind(content)
    return SlideSpec(
        kind=slide_kind,
        title=content.element_text,
        source_level=content.level,
        blocks=tuple(blocks),
    )
