from typing import (
    Optional, 
    Dict, 
    Any, 
    Self, 
    Iterator, 
    Iterable, 
    Type, 
    Optional, 
    cast,
    List as ListType,
)
import re

from ._typing import _AtMostOneNode, _InsertableElement, _OutElement

class Element:

    parent: Optional["Element"]
    next_element: _AtMostOneNode
    previous_element: _AtMostOneNode
    next_sibling: _AtMostOneNode
    previous_sibling: _AtMostOneNode

    contents: ListType[Type["Element"]] = []
    _decomposed: bool = False

    def setup(
        self,
        parent: Optional["Element"] = None,
        previous_element: _AtMostOneNode = None,
        next_element: _AtMostOneNode = None,
        previous_sibling: _AtMostOneNode = None,
        next_sibling: _AtMostOneNode = None,
    ) -> None:
        """Sets up the initial relations between this element and
        other elements.

        :param parent: The parent of this element.

        :param previous_element: The element parsed immediately before
            this one.

        :param next_element: The element parsed immediately before
            this one.

        :param previous_sibling: The most recently encountered element
            on the same level of the parse tree as this one.

        :param previous_sibling: The next element to be encountered
            on the same level of the parse tree as this one.
        """
        self.parent = parent

        self.previous_element = previous_element
        if self.previous_element is not None:
            self.previous_element.next_element = self

        self.next_element = next_element
        if self.next_element is not None:
            self.next_element.previous_element = self

        self.next_sibling = next_sibling
        if self.next_sibling is not None:
            self.next_sibling.previous_sibling = self

        if (
            previous_sibling is None
            and self.parent is not None
            and self.parent.contents
        ):
            previous_sibling = self.parent.contents[-1]

        self.previous_sibling = previous_sibling
        if self.previous_sibling is not None:
            self.previous_sibling.next_sibling = self

    def __deepcopy__(self, memo: Dict[Any, Any], recursive: bool = False) -> Self:
        raise NotImplementedError()

    def __copy__(self) -> Self:
        """A copy of a Element can only be a deep copy, because
        only one Element can occupy a given place in a parse tree.
        """
        return self.__deepcopy__({})
    
    default: Iterable[type["Element"]] = tuple()

    def _all_strings(
        self, 
        strip: bool = False,
        types: Iterable[Type["Element"]] = default
    ) -> Iterator[str]:
        """
        Yield all strings of certain classes, possibly stripping them.

        :param strip: Whether to remove markdown syntax.

        :param types: A tuple of Element subclasses. Any
            strings of a subclass not found in this list will be
            ignored.
        """
        raise NotImplementedError()

    @property
    def stripped_strings(self) -> Iterator[str]:
        """Yield all interesting strings in this Element, stripping them
        first.
        """
        for string in self._all_strings(True):
            yield string

    def get_text(
        self,
        separator: str = "\n",
        strip: bool = False,
        types: Iterable[Type["Element"]] = default,
    ) -> str:
        """Get all child strings of this Element, concatenated using the
        given separator.

        :param separator: Strings will be concatenated using this separator.

        :param strip: If True, strings will be stripped before being
            concatenated.

        :param types: A tuple of Element subclasses. Any
            strings of a subclass not found in this list will be
            ignored.

        :return: A string.
        """
        return separator.join([s for s in self._all_strings(strip, types=types)])

    text = property(get_text)
    getText = get_text

    def index(self, element: "Element") -> int:
        """Find the index of a child of this `Element` (by identity, not value).

        :param element: Look for this `Element` in this object's contents.
        """
        for i, child in enumerate(self.contents):
            if child is element:
                return i
        raise ValueError("Element.index: child not in this Element.")
    
    @property
    def is_empty_element(self) -> bool:
        return len(self.contents) == 0
    
    def extract(self, _self_index: Optional[int] = None) -> Self:
        """Destructively rips this element out of the tree.

        :param _self_index: The location of this element in its parent's
           .contents, if known. Passing this in allows for a performance
           optimization.

        :return: this `Element`, no longer part of the tree.
        """
        if self.parent is not None:
            if _self_index is None:
                _self_index = self.parent.index(self)
            del self.parent.contents[_self_index]

        last_child = self._last_descendant()

        last_child = cast(Element, last_child)
        next_element = last_child.next_element

        if self.previous_element is not None:
            if self.previous_element is not next_element:
                self.previous_element.next_element = next_element
        if next_element is not None and next_element is not self.previous_element:
            next_element.previous_element = self.previous_element
        self.previous_element = None
        last_child.next_element = None

        self.parent = None
        if (
            self.previous_sibling is not None
            and self.previous_sibling is not self.next_sibling
        ):
            self.previous_sibling.next_sibling = self.next_sibling
        if (
            self.next_sibling is not None
            and self.next_sibling is not self.previous_sibling
        ):
            self.next_sibling.previous_sibling = self.previous_sibling
        self.previous_sibling = self.next_sibling = None
        return self

    def decompose(self) -> None:
        """Recursively destroys this `Element` and its children.

        The element will be removed from the tree and wiped out; so
        will everything beneath it.

        The behavior of a decomposed `Element` is undefined and you
        should never use one for anything, but if you need to *check*
        whether an element has been decomposed, you can use the
        `Element.decomposed` property.
        """
        self.extract()
        e: _AtMostOneNode = self
        next_up: _AtMostOneNode = None
        while e is not None:
            next_up = e.next_element
            e.__dict__.clear()
            if isinstance(e, Element):
                e.contents = []
            e._decomposed = True
            e = next_up

    def clear(self, decompose: bool = False) -> None:
        """Destroy all children of this `Element` by calling
           `Element.extract` on them.

        :param decompose: If this is True, `Element.decompose` (a
            more destructive method) will be called instead of
            `Element.extract`.
        """
        for element in self.contents[:]:
            if decompose:
                element.decompose()
            else:
                element.extract()

    def _last_descendant(
        self, is_initialized: bool = True, accept_self: bool = True
    ) -> _AtMostOneNode:
        """Finds the last element beneath this object to be parsed.

        :param is_initialized: Is ``self`` initialized?

        :param accept_self: Is ``self`` an acceptable answer to the
            question?
        """
        if is_initialized and self.next_sibling is not None:
            last_child = self.next_sibling.previous_element
        else:
            last_child = self
            while isinstance(last_child, Element) and last_child.contents:
                last_child = last_child.contents[-1]
        if not accept_self and last_child is self:
            last_child = None
        return last_child

    def insert(self, position: int, *new_children: _InsertableElement) -> ListType[_OutElement]:
        """Insert one or more new Elements as a child of this `Element`.

        This works similarly to :py:meth:`list.insert`, except you can insert
        multiple elements at once.

        :param position: The numeric position that should be occupied.

        :param new_children: The Elements to insert.

        :return The newly inserted Elements.
        """
        inserted: ListType[Type[Element]] = []
        for new_child in new_children:
            inserted.extend(self._insert(position, new_child))
            position += 1
        return inserted

    def _insert(self, position: int, new_child: _InsertableElement) -> ListType["Element"]:
        if new_child is None:
            raise ValueError("Cannot insert None into a Element.")
        if new_child is self:
            raise ValueError("Cannot insert a Element into itself.")
        if isinstance(new_child, str):
            raise TypeError("Cannot insert a string into a Element. Please convert to an Element first.")
        
        from . import MarkdownDocument
        if isinstance(new_child, MarkdownDocument):
            return self.insert(position, *list(new_child.contents))
        position = min(position, len(self.contents))
        if hasattr(new_child, "parent") and new_child.parent is not None:
            if new_child.parent is self:
                current_index = self.index(new_child)
                if current_index < position:
                    position -= 1
                elif current_index == position:
                    return [new_child]
            new_child.extract()

        new_child.parent = self
        previous_child = None
        if position == 0:
            new_child.previous_sibling = None
            new_child.previous_element = self
        else:
            previous_child = self.contents[position - 1]
            new_child.previous_sibling = previous_child
            new_child.previous_sibling.next_sibling = new_child
            new_child.previous_element = previous_child._last_descendant(False)
        if new_child.previous_element is not None:
            new_child.previous_element.next_element = new_child

        new_childs_last_element = new_child._last_descendant(
            is_initialized=False, accept_self=True
        )
        
        new_childs_last_element = cast(Element, new_childs_last_element)

        if position >= len(self.contents):
            new_child.next_sibling = None

            parent: Optional[Element] = self
            parents_next_sibling = None
            while parents_next_sibling is None and parent is not None:
                parents_next_sibling = parent.next_sibling
                parent = parent.parent
                if parents_next_sibling is not None:
                    break
            if parents_next_sibling is not None:
                new_childs_last_element.next_element = parents_next_sibling
            else:
                # The last element of this element is the last element in
                # the document.
                new_childs_last_element.next_element = None
        else:
            next_child = self.contents[position]
            new_child.next_sibling = next_child
            if new_child.next_sibling is not None:
                new_child.next_sibling.previous_sibling = new_child
            new_childs_last_element.next_element = next_child

        if new_childs_last_element.next_element is not None:
            new_childs_last_element.next_element.previous_element = (
                new_childs_last_element
            )
        self.contents.insert(position, new_child)

        return [new_child]
    
    def append(self, element: _InsertableElement) -> "Element":
        """
        Appends the given `Element` to the contents of this `Element`.

        :param element: A eElement.

        :return The newly appended Element.
        """
        return self.insert(len(self.contents), element)[0]
    
    def __iter__(self) -> Iterator[_OutElement]:
        "Iterating over a Element iterates over its contents."
        return iter(self.contents)

    def __len__(self) -> int:
        "The length of a Element is the length of its list of contents."
        return len(self.contents)
    
    def __contains__(self, x: Any) -> bool:
        return x in self.contents
    
    def __getitem__(self, key: str) -> _OutElement:
        """tag[key] returns the value of the 'key' attribute for the Tag,
        and throws an exception if it's not there."""
        return self.contents[key]
    
    @property
    def next_elements(self) -> Iterator[_OutElement]:
        """
        All Elements that were parsed after this one.
        """
        i = self.next_element
        while i is not None:
            successor = i.next_element
            yield i
            i = successor
    @property
    def self_and_next_elements(self) -> Iterator[_OutElement]:
        """
        This Element, then all Elements that were parsed after it.
        """
        return self._self_and(self.next_elements)
    
    @property
    def next_siblings(self) -> Iterator[_OutElement]:
        """
        All Elements that are siblings of this one but were parsed
        later.
        """
        i = self.next_sibling
        while i is not None:
            successor = i.next_sibling
            yield i
            i = successor
    @property
    def previous_elements(self) -> Iterator[_OutElement]:
        """
        All Elements that were parsed before this one.

        :yield: A sequence of Elements.
        """
        i = self.previous_element
        while i is not None:
            successor = i.previous_element
            yield i
            i = successor

    @property
    def previous_siblings(self) -> Iterator[_OutElement]:
        """
        All Elements that are siblings of this one but were parsed
        earlier.

        :yield: A sequence of Elements.
        """
        i = self.previous_sibling
        while i is not None:
            successor = i.previous_sibling
            yield i
            i = successor
    
    @property
    def parents(self) -> Iterator[_OutElement]:
        """
        All elements that are parents of this Element.

        :yield: A sequence of Elements.
        """
        i = self.parent
        while i is not None:
            successor = i.parent
            yield i
            i = successor

    @property
    def self_and_parents(self) -> Iterator[_OutElement]:
        """
        This element, then all of its parents.

        :yield: A sequence of Elements, ending with a MarkdownDocument object.
        """
        return self._self_and(self.parents)

    def _self_and(self, other_generator:Iterator[_OutElement]) -> Iterator[_OutElement]:
        """
        Modify a generator by yielding this element, then everything
        yielded by the other generator.
        """
        yield self
        for i in other_generator:
            yield i

    @property
    def decomposed(self) -> bool:
        """
        Check whether a Element has been decomposed.
        """
        return getattr(self, "_decomposed", False) or False
    
    @property
    def children(self) -> Iterator[_OutElement]:
        """
        Iterate over all direct children of this `Element`.
        """
        return (x for x in self.contents)
    
    @property
    def self_and_descendants(self) -> Iterator[_OutElement]:
        """
        Iterate over this `Element` and its children in a
        breadth-first sequence.
        """
        return self._self_and(self.descendants)

    @property
    def descendants(self) -> Iterator[_OutElement]:
        """
        Iterate over all children of this `Element` in a
        breadth-first sequence.
        """
        if not len(self.contents):
            return
        # _last_descendant() can't return None here because
        # accept_self is True. Worst case, last_descendant will end up
        # as self.
        last_descendant = cast(Element, self._last_descendant(accept_self=True))
        stopNode = last_descendant.next_element
        current: _AtMostOneNode = self.contents[0]
        while current is not stopNode and current is not None:
            successor = current.next_element
            yield current
            current = successor
    

class Heading(Element):
    """Represents a heading element in a Markdown document."""

    element_text_source: Optional[str] = None

    def __init__(self, level: int, text: str):
        """Initializes a Heading object.

        :param level: The heading level (1-6).
        :param text: The text content of the heading.
        """
        self.setup()
        self.level = level
        self._text = text
    
    def _all_strings(self, strip = False, types = tuple()):
        for descendant in self.descendants:
            if not types or isinstance(descendant, types):
                text = descendant.element_text
                if isinstance(descendant, Heading) and not strip:
                    text = descendant.element_text_source
                if text:
                    yield text

    @property
    def element_text_source(self):
        if self.element_text_source is None:
            return "#" * self.level + self.element_text
        return self.element_text_source
    
    @property
    def element_text(self) -> str:
        return self._text
    
    @element_text.setter
    def heading_text(self, text: str):
        self._text = text

    def __repr__(self) -> str:
        return f"<Heading level={self.level} text='{self.text}'>"


class Paragraph(Element):
    """Represents a paragraph element in a Markdown document."""
    
    ORDERED_PATTERN = r'^[\s]*[-*+]\s+'
    UNORDERED_PATTERN = r'^[\s]*\d+\.\s+'

    def __init__(self, text: str):
        """Initializes a Paragraph object.

        :param text: The text content of the paragraph.
        """
        self.setup()
        self._text = text
    
    @property
    def element_text(self) -> str:
        return self._text
    
    @element_text.setter
    def element_text(self, text: str):
        self._text = text
    
    def _all_strings(self, strip = False, types = tuple()):
        if types:
            raise ValueError("Paragraph does not support types")
        if strip:
            # strip markdown syntax
            _text = re.sub(self.ORDERED_PATTERN, '', self._text)
            _text = re.sub(self.UNORDERED_PATTERN, '', _text).strip()

        yield _text

    def __repr__(self) -> str:
        return f"<Paragraph text='{self.text}'>"
    
class CodeBlock(Element):
    """Represents a code block element in a Markdown document."""

    def __init__(self, code: str, language: Optional[str] = None):
        """Initializes a CodeBlock object.

        :param code: The code content of the block.
        :param language: The programming language of the code block, if specified.
        """
        self.setup()
        self.code = code
        self.language = language
    
    @property
    def element_text(self) -> str:
        return self.code
    
    @element_text.setter
    def element_text(self, text: str):
        self.code = text

    @property
    def elelement_text_source(self):
        return f"```{self.language}\n{self.code}\n```"

    def _all_strings(self, strip = False, types = tuple()):
        if types:
            raise ValueError("CodeBlock does not support types")
        if strip:
            code_text = self.elelement_text_source.strip()
        yield code_text

    def __repr__(self) -> str:
        lang = f" language='{self.language}'" if self.language else ""
        return f"<CodeBlock{lang} code='{self.code[:30]}...'>"
    
class Table(Element):
    """Represents a table element in a Markdown document."""

    row_number = 0
    col_number = 0
    table_type: Optional[str] = None

    def __init__(self, headers: ListType[str], text: Optional[str] = None):
        """Initializes a Table object.

        :param headers: A list of header names for the table.
        """
        self.setup()
        self.headers = headers
        self._text: Optional[str] = text

    @property
    def element_text(self):
        return self._text
    
    @element_text.setter
    def element_text(self, text: str):
        self._text = text

    elelement_text_source = element_text

    def _all_strings(self, strip = False, types = tuple()):
        if types:
            raise ValueError("Table does not support types")
        if strip:
            _text = self._text.strip()
        yield _text

    def __repr__(self) -> str:
        return f"<Table headers={self.headers}>"

class Picture(Element):
    """Represents a picture element in a Markdown document."""

    def __init__(self, src: str, alt_text: Optional[str] = None, title: Optional[str] = None):
        """Initializes a Picture object.

        :param src: The source URL of the picture.
        :param alt_text: The alternative text for the picture.
        :param title: The title of the picture, if specified.
        """
        self.setup()
        self.src = src
        self.alt_text = alt_text
        self.title = title
    
    @property
    def element_text(self) -> str:
        return f"""![{self.alt_text}]({self.src} "{self.title}")"""
    
    @element_text.setter
    def element_text(self, text: str):
        return text
    
    elelement_text_source = element_text

    def _all_strings(self, strip = False, types = tuple()):
        if types:
            raise ValueError("Picture does not support types")
        if strip:
            element_text = self.element_text.strip()
        yield element_text
    
    def __repr__(self) -> str:
        alt = f" alt='{self.alt_text}'" if self.alt_text else ""
        title = f" title='{self.title}'" if self.title else ""
        return f"<Picture src='{self.src}'{alt}{title}>"

