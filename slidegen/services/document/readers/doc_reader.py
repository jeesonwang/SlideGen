from typing import Any

from .base import BaseDocumentReader, ContentType, DocumentReadResult
from .docx_reader import DocxReader
from .libreoffice import convert_with_soffice, is_soffice_available


class DocReader(BaseDocumentReader):
    """Reader for legacy Word files (.doc)."""

    @classmethod
    def get_supported_content_types(self) -> list[ContentType]:
        return [ContentType.DOC]

    def convert(self, local_path: str, **kwargs: Any) -> None | DocumentReadResult:
        extension = kwargs.get("file_extension", "").lower()
        supported_extensions = [ct.value for ct in DocReader.get_supported_content_types()]
        if extension not in supported_extensions:
            return None

        if not is_soffice_available():
            return None

        converted_path = convert_with_soffice(local_path, ".docx")
        if converted_path is None:
            return None

        return DocxReader().convert(converted_path, file_extension=".docx", **kwargs)
