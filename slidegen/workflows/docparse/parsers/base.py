from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any


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

    @abstractmethod
    def convert(self, local_path: str) -> None | DocumentParseResult:
        raise NotImplementedError("Subclasses must implement this method")
