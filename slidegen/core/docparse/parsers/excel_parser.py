import pandas as pd

from .base import DocumentParseResult
from .html_parser import HtmlParser


class ExcelParser(HtmlParser):
    """
    Parser for excel files.
    """

    def __init__(**kwargs):
        super().__init__(**kwargs)

    def convert(self, local_path, **kwargs) -> None | DocumentParseResult:
        
        extension = kwargs.get("file_extension", "").lower()
        if extension not in [".xlsx", ".xls"]:
            return None
        if extension == ".xlsx":
            sheets = pd.read_excel(local_path, sheet_name=None, engine="openpyxl")
            md_content = ""
            for s in sheets:
                md_content += f"## {s}\n"
                html_content = sheets[s].to_html(index=False)
                md_content += self._convert(html_content).text_content.strip() + "\n\n"
        else:
            sheets = pd.read_excel(local_path, sheet_name=None, engine="xlrd")
            md_content = ""
            for s in sheets:
                md_content += f"## {s}\n"
                html_content = sheets[s].to_html(index=False)
                md_content += self._convert(html_content).text_content.strip() + "\n\n"

        return DocumentParseResult(
            title=None,
            text_content=md_content,
        )
