from typing import (
    Any,
    Callable,
    Dict,
    IO,
    Iterable,
    Mapping,
    Optional,
    TYPE_CHECKING,
    Union,
    List
)

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from .elements import (
        Element,
        Paragraph,
        Heading,
        Table,
        CodeBlock,
        Picture
    )

_IncomingSource: TypeAlias = Union[str, bytes, IO[str], IO[bytes]]
_MarkdownNode: TypeAlias = Union["Element", "Paragraph", "Heading", "Table", "CodeBlock", "Picture"]
_AtMostOneNode: TypeAlias = Optional[_MarkdownNode]

_OutElement: TypeAlias = Union["Element", "Paragraph", "Heading", "Table", "CodeBlock", "Picture"]
_InsertableElement: TypeAlias = Union["Element", str]
