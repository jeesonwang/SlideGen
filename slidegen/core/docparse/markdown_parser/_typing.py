from typing_extensions import TypeAlias

from typing import (
    Any,
    Callable,
    Dict,
    IO,
    Iterable,
    Mapping,
    Optional,
    Pattern,
    Union,
    List as ListType
)
from elements import (
    Element,
    Paragraph,
    Heading,
    Table,
    Cell,
    Row,
    CodeBlock,
    Picture,
    MList,
    MListItem
)

_IncomingSource: TypeAlias = Union[str, bytes, IO[str], IO[bytes]]
_MarkdownNode: TypeAlias = Union["Element", "Paragraph", "Heading", "Table", "Cell", "Row", "CodeBlock", "Picture", "MList", "MListItem"]
_AtMostOneNode: TypeAlias = Optional[_MarkdownNode]

_OutElement: TypeAlias = Union["Element", "Paragraph", "Heading", "Table", "Cell", "Row", "CodeBlock", "Picture", "MList", "MListItem"]
_InsertableElement: TypeAlias = Union["Element", str]