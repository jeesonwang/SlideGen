from typing import IO, TYPE_CHECKING, Union

from typing import TypeAlias

if TYPE_CHECKING:
    from .elements import Element, Paragraph, Heading, Table, CodeBlock, Picture

_IncomingSource: TypeAlias = str | bytes | IO[str] | IO[bytes]
_MarkdownNode: TypeAlias = Union["Element", "Paragraph", "Heading", "Table", "CodeBlock", "Picture"]
_AtMostOneNode: TypeAlias = _MarkdownNode | None

_OutElement: TypeAlias = Union["Element", "Paragraph", "Heading", "Table", "CodeBlock", "Picture"]
_InsertableElement: TypeAlias = Union["Element", str]
