from typing import Any

from .base import BaseDocumentReader, ContentType, DocumentReadResult


class TextReader(BaseDocumentReader):
    """Reader for plain text files (.txt)."""

    @classmethod
    def get_supported_content_types(self) -> list[ContentType]:
        return [ContentType.TXT]

    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentReadResult:
        # Bail if not txt
        extension = kwargs.get("file_extension", "").lower()
        supported_extensions = [ct.value for ct in TextReader.get_supported_content_types()]
        if extension not in supported_extensions:
            return None

        with open(local_path, encoding="utf-8") as fh:
            text_content = fh.read()

        # Strip leading and trailing whitespace
        text_content = text_content.strip()

        return DocumentReadResult(
            title=None,  # Plain text files don't have titles
            text_content=text_content,
        )
