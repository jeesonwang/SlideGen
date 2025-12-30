import re
from typing import Any

from .base import ContentType, DocumentParser, DocumentParseResult


class MarkdownParser(DocumentParser):
    """Parser for Markdown files (.md, .markdown)."""

    @classmethod
    def get_supported_content_types(self) -> list[ContentType]:
        return [ContentType.MARKDOWN]

    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentParseResult:
        # Bail if not markdown
        extension = kwargs.get("file_extension", "").lower()
        supported_extensions = [ct.value for ct in MarkdownParser.get_supported_content_types()]
        if extension not in supported_extensions:
            return None

        with open(local_path, encoding="utf-8") as fh:
            text_content = fh.read()

        # Strip leading and trailing whitespace
        text_content = text_content.strip()

        # Try to extract title from the first heading
        title = None
        # Match the first H1 heading (# Title)
        title_match = re.match(r"^#\s+(.+?)$", text_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        return DocumentParseResult(
            title=title,
            text_content=text_content,
        )
