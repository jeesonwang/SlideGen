from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from slidegen.services.document.markdown import Heading
from slidegen.services.slidegen.outline_structure import ChapterSlideGroup


@dataclass(frozen=True)
class PlannedContentSlide:
    """Metadata for a single content slide within a chapter."""

    heading: Heading
    slide_index: int
    sequence_number: int
    total_content_slides: int


@dataclass(frozen=True)
class PlannedChapter:
    """A chapter with its home slide and all associated content slides."""

    heading: Heading
    chapter_number: int
    home_slide_index: int
    content_slides: tuple[PlannedContentSlide, ...]


@dataclass(frozen=True)
class PresentationRenderPlan:
    """Complete render plan encompassing catalog, chapter homes, content slides, and end slide layout."""

    catalog_last_index: int
    chapters: tuple[PlannedChapter, ...]
    end_slide_index: int

    @property
    def total_chapters(self) -> int:
        return len(self.chapters)

    @property
    def total_content_slides(self) -> int:
        return sum(len(chapter.content_slides) for chapter in self.chapters)


@dataclass(frozen=True)
class ConversionSummary:
    """Summary of a completed presentation conversion for reporting."""

    title: str
    total_slides: int
    total_chapters: int
    total_content_slides: int
    catalog_slide_count: int
    native_fallback_roles: tuple[str, ...]
    elapsed_seconds: float


def build_presentation_render_plan(
    chapter_slide_groups: Sequence[ChapterSlideGroup],
    *,
    catalog_last_index: int,
) -> PresentationRenderPlan:
    """Build a render plan from chapter slide groups."""

    current_slide_index = catalog_last_index + 1
    total_content_slides = sum(len(group.slides) for group in chapter_slide_groups)
    planned_chapters: list[PlannedChapter] = []
    content_sequence_number = 0

    for chapter_number, group in enumerate(chapter_slide_groups, start=1):
        home_slide_index = current_slide_index
        current_slide_index += 1
        planned_content_slides: list[PlannedContentSlide] = []

        for slide in group.slides:
            content_sequence_number += 1
            planned_content_slides.append(
                PlannedContentSlide(
                    heading=slide,
                    slide_index=current_slide_index,
                    sequence_number=content_sequence_number,
                    total_content_slides=total_content_slides,
                )
            )
            current_slide_index += 1

        planned_chapters.append(
            PlannedChapter(
                heading=group.chapter,
                chapter_number=chapter_number,
                home_slide_index=home_slide_index,
                content_slides=tuple(planned_content_slides),
            )
        )

    return PresentationRenderPlan(
        catalog_last_index=catalog_last_index,
        chapters=tuple(planned_chapters),
        end_slide_index=current_slide_index,
    )
