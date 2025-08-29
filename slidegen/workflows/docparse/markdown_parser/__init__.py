import os
import re
from collections.abc import Iterable, Iterator
from typing import Any

from ._typing import _IncomingSource
from .elements import CodeBlock, Element, Heading, Paragraph, Picture, Table

__all__ = ["Heading", "MarkdownDocument", "MarkdownParser"]


class MarkdownDocument(Element):
    ROOT_ELEMENT_NAME: str = "[markdowndocument]"

    def __init__(self, source: _IncomingSource, **kwargs: Any):
        super().__init__(**kwargs)
        self.main: Heading | None = None

        if hasattr(source, "read"):  # It's a file-type object.
            source = source.read()
        elif isinstance(source, bytes):
            source = source.decode()
        elif isinstance(source, str):
            if os.path.isfile(source) and source.endswith(".md"):
                with open(source, encoding="utf-8") as f:
                    source = f.read()
        if source and isinstance(source, str):
            self._parse(source)

    def _parse(self, markdown_text: str) -> None:
        parser = MarkdownParser(self)
        parser.parse(markdown_text)

    def _all_strings(self, strip: bool = False, types: Iterable[type[Element]] = ()) -> Iterator[str]:
        for child in self.descendants:
            if not types or any(isinstance(child, t) for t in types):
                if strip:
                    yield child.element_text.strip()
                else:
                    yield child.element_text_source

    @property
    def title(self) -> str:
        return self.main.text if self.main is not None else ""

    def __str__(self) -> str:
        return "<MarkdownDocument title={self.title}>"

    def __repr__(self) -> str:
        return self.__str__()


class MarkdownParser:
    table_type: str | None
    previous_heading: MarkdownDocument | Heading

    def __init__(self, document: MarkdownDocument):
        self.document = document
        self.previous_heading = document
        self.in_code_block = False
        self.in_table_block = False
        self.table_lines: list[str] = []

        self.code_language: str | None = None
        self.code_lines: list[str] = []

        self.jump_to_next = False

    def parse(self, markdown_text: str) -> None:
        strings = markdown_text.split("\n")
        for index in range(len(strings)):
            if self.jump_to_next:
                self.jump_to_next = False
                continue
            line = strings[index]
            next_line = strings[index + 1] if index + 1 < len(strings) else None
            if self.in_table_block:
                self.process_table_row(line, next_line)
            else:
                self.process_line(line.rstrip() if not self.in_code_block else line, next_line)

    def process_line(self, line: str, next_line: str | None = None) -> None:
        if self.in_code_block:
            if line.startswith("```"):
                self.end_code_block()
            else:
                self.code_lines.append(line)
            return

        handlers = [
            self.process_code_block_start,
            self.process_heading,
            self.process_list,
            self.process_table,
            self.process_image,
            self.process_paragraph,
        ]

        for handler in handlers:
            if handler(line, next_line):
                return

    def process_code_block_start(self, line: str, next_line: str | None = None) -> bool:
        match = re.search(r"^\s*```(\w+)?", line)
        if match:
            self.in_code_block = True
            self.code_language = match.group(1)
            self.code_lines = []
            return True
        return False

    def end_code_block(self) -> None:
        code = "\n".join(self.code_lines)
        code_block = CodeBlock(code, language=self.code_language)
        self.previous_heading.append(code_block)
        self.in_code_block = False
        self.code_language = None

    def process_heading(self, line: str, next_line: str | None = None) -> bool:
        is_heading = False
        for level in range(1, 3):
            is_heading = self._parse_heading_var_one(level, line, next_line)
            if is_heading:
                break
        if is_heading:
            self.jump_to_next = True
            return is_heading

        for level in range(1, 7):
            is_heading = self._parse_heading_var_two(level, line)
            if is_heading:
                break
        return is_heading

    def process_list(self, line: str, next_line: str | None = None) -> bool:
        stripped_line = line.lstrip()

        list_match = re.match(r"^([\*\-\+])\s+(.*)", stripped_line)
        if list_match:
            self.handle_list(list_match)
            return True

        olist_match = re.match(r"^(\d+)[\.\)]\s+(.*)", stripped_line)
        if olist_match:
            self.handle_list(olist_match)
            return True

        return False

    def handle_list(self, match: re.Match[str]) -> None:
        # bullet = match.group(1)
        text = match.group(2).strip()

        item = Paragraph(text)
        self.previous_heading.append(item)

    def process_table(self, line: str, next_line: str | None = None) -> bool:
        if self.is_markdown_table_start(line, next_line):
            self.in_table_block = True
            self.table_type = "markdown"
            if next_line is not None:
                self.table_lines = [line, next_line]
            else:
                self.table_lines = [line]
            self.jump_to_next = True  # Skip the separator line
            return True
        elif line.strip().startswith("<table"):
            self.in_table_block = True
            self.table_type = "html"
            self.table_lines = [line]
            return True
        return False

    def is_markdown_table_start(self, line: str, next_line: str | None) -> bool:
        if not line.strip().startswith("|") or not line.strip().endswith("|"):
            return False
        if not next_line:
            return False
        separator = next_line.strip()
        if not separator.startswith("|") or not separator.endswith("|"):
            return False
        parts = separator.split("|")[1:-1]
        for part in parts:
            if not re.match(r"^\s*:?-+:\s*$", part.strip()):
                return False
        return True

    def process_table_row(self, line: str, next_line: str | None) -> None:
        if self.table_type == "markdown":
            stripped = line.strip()
            if not stripped or not stripped.startswith("|"):
                self.end_table()
                return
            self.table_lines.append(line)
            if not next_line or not next_line.strip().startswith("|"):
                self.end_table()
        elif self.table_type == "html":
            self.table_lines.append(line)
            if "</table>" in line:
                self.end_table()

    def end_table(self) -> None:
        if self.table_type == "markdown":
            self.parse_markdown_table()
        elif self.table_type == "html":
            self.parse_html_table()
        self.in_table_block = False
        self.table_type = None
        self.table_lines = []

    def parse_markdown_table(self) -> None:
        lines = [line.strip() for line in self.table_lines if line is not None]
        headers = [h.strip() for h in lines[0].split("|")[1:-1]]
        row_number = len(lines)
        col_number = len(headers)

        table = Table(headers=headers)
        table.table_type = "markdown"
        table.text = "\n".join(lines)
        table.row_number = row_number
        table.col_number = col_number
        self.previous_heading.append(table)

    def parse_html_table(self) -> None:
        html = "\n".join(self.table_lines)
        table = Table(headers=[])
        table.table_type = "html"
        # Extract headers
        headers = []
        thead_match = re.search(r"<thead>(.*?)</thead>", html, re.DOTALL)
        if thead_match:
            thead_content = thead_match.group(1)
            headers = re.findall(r"<th>(.*?)</th>", thead_content, re.DOTALL)
            headers = [re.sub(r"<[^>]+>", "", h).strip() for h in headers]
        table.headers = headers
        # Extract rows
        rows = []
        tbody_match = re.search(r"<tbody>(.*?)</tbody>", html, re.DOTALL)
        if tbody_match:
            tbody_content = tbody_match.group(1)
            tr_matches = re.findall(r"<tr>(.*?)</tr>", tbody_content, re.DOTALL)
            for tr in tr_matches:
                tds = re.findall(r"<td>(.*?)</td>", tr, re.DOTALL)
                cells = [re.sub(r"<[^>]+>", "", td).strip() for td in tds]
                rows.append(cells)
        else:
            tr_matches = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)
            for tr in tr_matches:
                if "<th>" in tr:
                    continue  # Already handled headers
                tds = re.findall(r"<td>(.*?)</td>", tr, re.DOTALL)
                cells = [re.sub(r"<[^>]+>", "", td).strip() for td in tds]
                rows.append(cells)
        table.text = html
        table.row_number = len(rows)
        table.col_number = len(headers)
        self.previous_heading.append(table)

    def process_image(self, line: str, next_line: str | None = None) -> bool:
        match = re.match(r"!\[(.*?)\]\((.*?)\s*(?:\"(.*?)\")?\)", line)
        if match:
            alt = match.group(1)
            src = match.group(2)
            title = match.group(3)
            picture = Picture(src, alt_text=alt, title=title)
            self.previous_heading.append(picture)
            return True
        return False

    def process_paragraph(self, line: str, next_line: str | None = None) -> bool:
        if not line.strip():
            return False
        paragraph = Paragraph(line)
        # 使用基类append方法
        self.previous_heading.append(paragraph)
        return True

    def _parse_heading_var_one(self, level: int, string: str, next_string: str | None) -> bool:
        if next_string is None or re.search(r"^\s*$", string) is not None:
            return False

        if level == 1:
            tmpl = "="
        elif level == 2:
            tmpl = "-"
        else:
            raise Exception(f"Not support level: {level}")

        regex = rf"^{tmpl}{{3,}}\s*$"
        result = re.search(regex, next_string)

        if result is None:
            return False

        return self._parse_heading_action(level=level, text=string.strip(), text_source=f"{string}\n{next_string}")

    def _parse_heading_var_two(self, level: int, string: str) -> bool:
        regex = rf"^(\s?#{{{level}}}\s+)(.*)$"
        result = re.search(regex, string)

        if result is None:
            return False

        return self._parse_heading_action(level=level, text=result[2], text_source=result[1] + result[2])

    def _parse_heading_action(self, level: int, text: str, text_source: str) -> bool:
        cur_heading = Heading(level, text)
        cur_heading.element_text_source = text_source
        if self.previous_heading is self.document:
            self.previous_heading.append(cur_heading)
        elif isinstance(self.previous_heading, Heading):
            if level > self.previous_heading.level:
                self.previous_heading.append(cur_heading)
            else:
                parent = self.previous_heading.parent
                while parent.level >= level:  # type: ignore
                    parent = parent.parent  # type: ignore
                parent.append(cur_heading)  # type: ignore
        if cur_heading.level == 1:
            self.document.main = cur_heading
        self.previous_heading = cur_heading
        return True
