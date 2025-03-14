import copy
import mimetypes
import os
import re
from typing import List, Optional, Tuple, Union
import traceback

import puremagic
from loguru import logger

from exception.custom_exception import FileParseError, FileTypeError
from .parsers import (
    DocumentParser,
    DocumentParseResult,
    DocxParser,
    HtmlParser,
    ExcelParser,
)

mimetypes.add_type("text/csv", ".csv")

class MarkdownConverter:

    def __init__(self):
        self.document_parsers: List[DocumentParser] = []

    def _convert(
        self, local_path: str, extensions: List[Union[str, None]], **kwargs
    ) -> DocumentParseResult:
        error_trace = ""

        for ext in extensions + [None]:  # Try last with no extension
            for converter in self.document_parsers:
                _kwargs = copy.deepcopy(kwargs)

                if ext is None:
                    if "file_extension" in _kwargs:
                        del _kwargs["file_extension"]
                else:
                    _kwargs.update({"file_extension": ext})


                try:
                    res = converter.convert(local_path, **_kwargs)
                except Exception:
                    error_trace = ("\n\n" + traceback.format_exc()).strip()

                if res is not None:
                    res.text_content = "\n".join(
                        [line.rstrip() for line in re.split(r"\r?\n", res.text_content)]
                    )
                    res.text_content = re.sub(r"\n{3,}", "\n\n", res.text_content)
                    return res
                
        if len(error_trace) > 0:
            raise FileParseError(
                f"Could not convert '{local_path}' to Markdown. File type was recognized as {extensions}. While converting the file, the following error was encountered:\n\n{error_trace}"
            )

        raise FileTypeError(
            f"Could not convert '{local_path}' to Markdown. The formats {extensions} are not supported."
        )

    def register_parser(self, parser: DocumentParser) -> None:
        """Register a page text converter."""
        self._page_converters.insert(0, parser)

    def _guess_ext_magic(self, path):
        """Use puremagic (a Python implementation of libmagic) to guess a file's extension based on the first few bytes."""
        # Use puremagic to guess
        try:
            guesses = puremagic.magic_file(path)

            if len(guesses) == 0:
                with open(path, "rb") as file:
                    while True:
                        char = file.read(1)
                        if not char:  # End of file
                            break
                        if not char.isspace():
                            file.seek(file.tell() - 1)
                            break
                    try:
                        guesses = puremagic.magic_stream(file)
                    except puremagic.main.PureError:
                        pass

            extensions = list()
            for g in guesses:
                ext = g.extension.strip()
                if len(ext) > 0:
                    if not ext.startswith("."):
                        ext = "." + ext
                    if ext not in extensions:
                        extensions.append(ext)
            return extensions
        except FileNotFoundError:
            pass
        except IsADirectoryError:
            pass
        except PermissionError:
            pass
        return []