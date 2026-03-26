from typing import Any

from .base import BaseDocumentReader, ContentType, DocumentReadResult
from .libreoffice import convert_with_soffice, is_soffice_available
from .pptx_reader import PptxReader


class PptReader(BaseDocumentReader):
    """Reader for legacy PowerPoint files (.ppt)."""

    @classmethod
    def get_supported_content_types(self) -> list[ContentType]:
        return [ContentType.PPT]

    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentReadResult:
        extension = kwargs.get("file_extension", "").lower()
        supported_extensions = [ct.value for ct in PptReader.get_supported_content_types()]
        if extension not in supported_extensions:
            return None

        if not is_soffice_available():
            return None

        converted_path = convert_with_soffice(local_path, ".pptx")
        if converted_path is None:
            return None

        return PptxReader().convert(converted_path, file_extension=".pptx", **kwargs)
