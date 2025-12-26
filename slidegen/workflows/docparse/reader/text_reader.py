from typing import Any

from .base import ContentType, DocumentParser, DocumentParseResult


class TextParser(DocumentParser):
    """Parser for plain text files (.txt)."""

    @classmethod
    def get_supported_content_types(self) -> list[ContentType]:
        return [ContentType.TXT]

    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentParseResult:
        # Bail if not txt
        extension = kwargs.get("file_extension", "").lower()
        supported_extensions = [ct.value for ct in TextParser.get_supported_content_types()]
        if extension not in supported_extensions:
            return None

        with open(local_path, encoding="utf-8") as fh:
            text_content = fh.read()

        # Strip leading and trailing whitespace
        text_content = text_content.strip()

        return DocumentParseResult(
            title=None,  # Plain text files don't have titles
            text_content=text_content,
        )
