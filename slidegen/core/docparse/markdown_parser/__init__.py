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

class MarkdownDocument(Element):
    ROOT_ELEMENT_NAME: str = "[markdowndocument]"
    
    def __init__(self):
        super().__init__()
        self.main: Heading | None = None

    @property
    def title(self) -> str:
        return self.main.text if self.main is not None else ''

    def __str__(self):
        return 'MarkdownDocument(title=%s)' % self.title