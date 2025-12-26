from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class ContentType(str, Enum):
    """Enum for content types supported by knowledge readers."""

    # Generic types
    FILE = "file"
    URL = "url"
    TEXT = "text"
    TOPIC = "topic"
    YOUTUBE = "youtube"

    # Document file extensions
    PDF = ".pdf"
    TXT = ".txt"
    MARKDOWN = ".md"
    DOCX = ".docx"
    DOC = ".doc"
    JSON = ".json"
    HTML = ".html"
    HTM = ".htm"

    # Spreadsheet file extensions
    CSV = ".csv"
    XLSX = ".xlsx"
    XLS = ".xls"


def get_content_type_enum(content_type_str: str) -> ContentType:
    """Convert a content type string to ContentType enum."""
    return ContentType(content_type_str)


@dataclass
class DocumentParseResult:
    """The result of parsing a document."""

    text_content: str
    title: str | None = None

    def asdict(self) -> dict[str, Any]:
        """Convert the DocumentParseResult to a dictionary."""
        return asdict(self)


class DocumentParser(ABC):
    """Base class for document parsers."""

    @classmethod
    def get_supported_content_types(self) -> list[ContentType]:
        raise NotImplementedError("Subclasses must implement this method")

    @abstractmethod
    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentParseResult:
        raise NotImplementedError("Subclasses must implement this method")
