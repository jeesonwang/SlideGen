import re
from typing import Any
from urllib.parse import quote, unquote, urlparse, urlunparse

import markdownify


class CustomMarkdownify(markdownify.MarkdownConverter):  # type: ignore
    """
    A custom version of markdownify's MarkdownConverter. Changes include:

    - Altering the default heading style to use '#', '##', etc.
    - Removing javascript hyperlinks.
    - Truncating images with large data:uri sources.
    - Ensuring URIs are properly escaped, and do not conflict with Markdown syntax.
    - The table remains as an html table.
    """

    _remain_html_table = True

    def __init__(self, **options: Any):
        options["heading_style"] = options.get("heading_style", markdownify.ATX)
        if "html_table" in options:
            html_table = options.get("html_table")
            self._remain_html_table = html_table  # type: ignore
        # Explicitly cast options to the expected type if necessary
        super().__init__(**options)

    def convert_hn(self, n: int, el: Any, text: str, convert_as_inline: bool) -> str:
        """Same as usual, but be sure to start with a new line"""
        if not convert_as_inline:
            if not re.search(r"^\n", text):
                return "\n" + super().convert_hn(n, el, text, convert_as_inline)  # type: ignore

        return super().convert_hn(n, el, text, convert_as_inline)  # type: ignore

    def convert_a(self, el: Any, text: str, convert_as_inline: bool) -> str:
        """Same as usual converter, but removes Javascript links and escapes URIs.
        From https://github.com/microsoft/markitdown/blob/main/packages/markitdown/src/markitdown/converters/_markdownify.py
        """
        prefix, suffix, text = markdownify.chomp(text)  # type: ignore
        if not text:
            return ""

        if el.find_parent("pre") is not None:
            return text

        href = el.get("href")
        title = el.get("title")

        # Escape URIs and skip non-http or file schemes
        if href:
            try:
                parsed_url = urlparse(href)  # type: ignore
                if parsed_url.scheme and parsed_url.scheme.lower() not in ["http", "https", "file"]:  # type: ignore
                    return "%s%s%s" % (prefix, text, suffix)
                href = urlunparse(parsed_url._replace(path=quote(unquote(parsed_url.path))))  # type: ignore
            except ValueError:  # It's not clear if this ever gets thrown
                return "%s%s%s" % (prefix, text, suffix)

        # For the replacement see #29: text nodes underscores are escaped
        if (
            self.options["autolinks"]
            and text.replace(r"\_", "_") == href
            and not title
            and not self.options["default_title"]
        ):
            # Shortcut syntax
            return "<%s>" % href
        if self.options["default_title"] and not title:
            title = href
        title_part = ' "%s"' % title.replace('"', r"\"") if title else ""
        return "%s[%s](%s%s)%s" % (prefix, text, href, title_part, suffix) if href else text

    def convert_img(self, el: Any, text: str, convert_as_inline: bool) -> str:
        """Same as usual converter, but removes data URIs"""

        alt = el.attrs.get("alt", None) or ""
        src = el.attrs.get("src", None) or ""
        title = el.attrs.get("title", None) or ""
        title_part = ' "%s"' % title.replace('"', r"\"") if title else ""
        if convert_as_inline and el.parent.name not in self.options["keep_inline_images_in"]:
            return alt

        # Remove dataURIs
        if src.startswith("data:"):
            src = src.split(",")[0] + "..."

        return "![%s](%s%s)" % (alt, src, title_part)

    def convert_table(self, el: Any, text: str, convert_as_inline: bool) -> str:
        if self._remain_html_table:
            text = "<table>" + text + "</table>"
        else:
            text = super().convert_table(el, text, convert_as_inline)
        return text.strip()

    def convert_th(self, el: Any, text: str, convert_as_inline: bool) -> str:
        if self._remain_html_table:
            attrs = " ".join(f'{k}="{v}"' for k, v in el.attrs.items())
            if attrs:
                text = f"<th {attrs}>{text.strip()}</th>".replace("\n", " ")
            else:
                text = f"<th>{text.strip()}</th>".replace("\n", " ")
        else:
            text = super().convert_th(el, text, convert_as_inline)
        return text.strip()

    def convert_td(self, el: Any, text: str, convert_as_inline: bool) -> str:
        if self._remain_html_table:
            attrs = " ".join(f'{k}="{v}"' for k, v in el.attrs.items())
            if attrs:
                text = f"<td {attrs}>{text.strip()}</td>".replace("\n", " ")
            else:
                text = f"<td>{text.strip()}</td>".replace("\n", " ")
        else:
            text = super().convert_td(el, text, convert_as_inline)
        return text.strip().replace("\n", " ")

    def convert_tr(self, el: Any, text: str, convert_as_inline: bool) -> str:
        if self._remain_html_table:
            text = "<tr>" + text + "</tr>"
        else:
            text = super().convert_tr(el, text, convert_as_inline)
        return text.strip()
