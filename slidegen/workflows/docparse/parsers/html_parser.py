from typing import Any

from bs4 import BeautifulSoup

from ._markdownify import CustomMarkdownify
from .base import DocumentParser, DocumentParseResult


class HtmlParser(DocumentParser):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.html_table = kwargs.get("html_table", True)

    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentParseResult:
        # Bail if not html
        extension = kwargs.get("file_extension", "")
        if extension.lower() not in [".html", ".htm"]:
            return None

        result = None
        with open(local_path, encoding="utf-8") as fh:
            result = self._convert(fh.read())

        return result

    def _convert(self, html_content: str) -> DocumentParseResult:
        soup = BeautifulSoup(html_content, "html.parser")
        # Remove javascript and style blocks
        for script in soup(["script", "style"]):
            script.extract()

        markdownify = CustomMarkdownify(html_table=self.html_table)
        body_elm = soup.find("body")
        webpage_text = ""
        if body_elm:
            webpage_text = markdownify.convert_soup(body_elm)
        else:
            webpage_text = markdownify.convert_soup(soup)

        assert isinstance(webpage_text, str)

        # remove leading and trailing \n
        webpage_text = webpage_text.strip()

        return DocumentParseResult(
            title=None if soup.title is None else soup.title.string,
            text_content=webpage_text,
        )
