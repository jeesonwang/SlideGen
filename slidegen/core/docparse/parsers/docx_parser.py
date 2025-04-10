import mammoth

from .base import (
    DocumentParseResult,
)
from .html_parser import HtmlParser


class DocxParser(HtmlParser):
    """
    DOCX parser
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def convert(self, local_path, **kwargs) -> None | DocumentParseResult:
        # Bail if not a DOCX
        extension = kwargs.get("file_extension", "")
        if extension.lower() != ".docx":
            return None

        result = None
        with open(local_path, "rb") as docx_file:
            style_map = kwargs.get("style_map", None)
            result = mammoth.convert_to_html(docx_file, style_map=style_map)
            html_content = result.value
            result = self._convert(html_content)

        return result
