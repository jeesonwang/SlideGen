from typing import Any

import pandas as pd

from .base import ContentType, DocumentReadResult
from .html_reader import HtmlReader


class ExcelReader(HtmlReader):
    """
    Reader for Excel files.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @classmethod
    def get_supported_content_types(self) -> list[ContentType]:
        return [ContentType.XLSX, ContentType.XLS]

    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentReadResult:
        extension = kwargs.get("file_extension", "").lower()
        supported_extensions = [ct.value for ct in ExcelReader.get_supported_content_types()]
        if extension not in supported_extensions:
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

        return DocumentReadResult(
            title=None,
            text_content=md_content,
        )
