from typing import Any

import mammoth

from .base import (
    ContentType,
    DocumentReadResult,
)
from .html_reader import HtmlReader


class DocxReader(HtmlReader):
    """
    DOCX reader
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def get_supported_content_types(self) -> list[ContentType]:
        return [ContentType.DOCX]

    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentReadResult:
        # Bail if not a DOCX
        extension = kwargs.get("file_extension", "").lower()
        supported_extensions = [ct.value for ct in DocxReader.get_supported_content_types()]
        if extension not in supported_extensions:
            return None

        with open(local_path, "rb") as docx_file:
            style_map = kwargs.get("style_map", None)
            mammoth_result = mammoth.convert_to_html(docx_file, style_map=style_map)
            html_content = mammoth_result.value
            converted: DocumentReadResult = self._convert(html_content)

        return converted
