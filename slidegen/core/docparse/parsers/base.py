from abc import ABC
from dataclasses import asdict, dataclass
from typing import Any, Union


@dataclass
class DocumentParseResult:
    """The result of parsing a document."""

    text_content: str
    title: Union[str, None] = None

    def asdict(self) -> dict[str, Any]:
        """Convert the DocumentParseResult to a dictionary."""
        return asdict(self)


class DocumentParser(ABC):
    """Base class for document parsers."""

    def __init__(self, **kwargs: Any) -> None:
        pass

    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentParseResult:
        raise NotImplementedError("Subclasses must implement this method")
