from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pptx import Presentation
from pptx.util import Pt


@dataclass
class SlideGeometryIssue:
    level: Literal["error", "warning"]
    slide_index: int
    message: str
    shapes_involved: tuple[str, ...] = ()


class PostRenderValidator:
    def __init__(self, mode: Literal["off", "warn", "fail"] = "warn"):
        self.mode = mode

    def validate(self, prs: Presentation) -> list[SlideGeometryIssue]:
        if self.mode == "off":
            return []
        issues: list[SlideGeometryIssue] = []
        for i, slide in enumerate(prs.slides):
            issues.extend(self._check_out_of_bounds(slide, i, int(prs.slide_width), int(prs.slide_height)))
            issues.extend(self._check_readability(slide, i))
        return issues

    def _check_out_of_bounds(self, slide, index: int, slide_w: int, slide_h: int) -> list[SlideGeometryIssue]:
        issues = []
        for shape in slide.shapes:
            left = shape.left
            top = shape.top
            right = left + shape.width
            bottom = top + shape.height
            if left < 0 or top < 0 or right > slide_w or bottom > slide_h:
                issues.append(SlideGeometryIssue(
                    level="error" if self.mode == "fail" else "warning",
                    slide_index=index,
                    message=f"Shape '{shape.name}' extends beyond slide boundaries",
                    shapes_involved=(shape.name,),
                ))
        return issues

    def _check_readability(self, slide, index: int) -> list[SlideGeometryIssue]:
        issues = []
        min_size = Pt(8)
        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue
            for para in shape.text_frame.paragraphs:
                if para.font.size and para.font.size < min_size:
                    issues.append(SlideGeometryIssue(
                        level="warning",
                        slide_index=index,
                        message=f"Text in shape '{shape.name}' is smaller than 8pt",
                        shapes_involved=(shape.name,),
                    ))
                for run in para.runs:
                    if run.font.size and run.font.size < min_size:
                        issues.append(SlideGeometryIssue(
                            level="warning",
                            slide_index=index,
                            message=f"Text in shape '{shape.name}' is smaller than 8pt",
                            shapes_involved=(shape.name,),
                        ))
        return issues
