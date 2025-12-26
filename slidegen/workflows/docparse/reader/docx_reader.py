from typing import Any

import mammoth

from .base import (
    ContentType,
    DocumentParseResult,
)
from .html_reader import HtmlParser


class DocxParser(HtmlParser):
    """
    DOCX parser
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def get_supported_content_types(self) -> list[ContentType]:
        return [ContentType.DOCX]

    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentParseResult:
        # Bail if not a DOCX
        extension = kwargs.get("file_extension", "").lower()
        supported_extensions = [ct.value for ct in DocxParser.get_supported_content_types()]
        if extension not in supported_extensions:
            return None

        result = None
        with open(local_path, "rb") as docx_file:
            style_map = kwargs.get("style_map", None)
            result = mammoth.convert_to_html(docx_file, style_map=style_map)
            html_content = result.value
            result = self._convert(html_content)

        return result
