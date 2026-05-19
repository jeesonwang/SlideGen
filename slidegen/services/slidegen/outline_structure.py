from collections.abc import Iterator
from dataclasses import dataclass

from slidegen.services.document.markdown import Heading


@dataclass(frozen=True)
class ChapterSlideGroup:
    chapter: Heading
    slides: list[Heading]
    is_nested: bool


def _direct_heading_children(heading: Heading, level: int) -> list[Heading]:
    return [child for child in heading.children if isinstance(child, Heading) and child.level == level]


def _has_topic_headings(section: Heading) -> bool:
    return any(isinstance(child, Heading) and child.level >= 4 for child in section.children)


def iter_chapter_slide_groups(main_heading: Heading | None) -> Iterator[ChapterSlideGroup]:
    if main_heading is None:
        return

    chapters = _direct_heading_children(main_heading, 2)
    for chapter in chapters:
        candidate_sections = _direct_heading_children(chapter, 3)
        has_nested_sections = any(_has_topic_headings(section) for section in candidate_sections)
        if has_nested_sections:
            yield ChapterSlideGroup(chapter=chapter, slides=candidate_sections, is_nested=True)
        else:
            yield ChapterSlideGroup(chapter=chapter, slides=[chapter], is_nested=False)


def content_slides(main_heading: Heading | None) -> list[Heading]:
    slides: list[Heading] = []
    for group in iter_chapter_slide_groups(main_heading):
        slides.extend(group.slides)
    return slides
