import copy
import os
import re
import tempfile
import traceback
from pathlib import Path
from typing import Any, BinaryIO

import puremagic
from loguru import logger

from slidegen.exception import FileParseError, FileTypeError

from .parsers import (
    DocumentParser,
    DocumentParseResult,
    DocxParser,
    ExcelParser,
    HtmlParser,
    PdfParser,
    TextParser,
)


class MarkdownConverter:
    """Convert file to markdown"""

    def __init__(self) -> None:
        self._builtins_enabled = False
        self.document_parsers: list[DocumentParser] = []
        self.register_builtins()

    def register_builtins(self, **kwargs: Any) -> None:
        if not self._builtins_enabled:
            self.register_parser(DocxParser())
            self.register_parser(HtmlParser())
            self.register_parser(ExcelParser())
            self.register_parser(PdfParser())
            self.register_parser(TextParser())
            # TODO: Add more parsers here
            self._builtins_enabled = True
        else:
            logger.warning("Builtins parsers already registered")

    def convert_local(self, path: str | Path, **kwargs: Any) -> DocumentParseResult:
        if isinstance(path, Path):
            path = str(path)

        ext = kwargs.get("file_extension")
        extensions = [ext] if ext is not None else []

        base, ext = os.path.splitext(path)
        self._append_ext(extensions, ext)

        for g in self._guess_ext_magic(path):
            self._append_ext(extensions, g)

        # Convert
        return self._convert(path, extensions, **kwargs)

    def convert_stream(self, stream: BinaryIO, **kwargs: Any) -> DocumentParseResult:
        ext = kwargs.get("file_extension")
        extensions = [ext] if ext is not None else []

        # Save the file locally to a temporary file. It will be deleted before this method exits
        handle, temp_path = tempfile.mkstemp()
        fh = os.fdopen(handle, "wb")
        result = None
        try:
            # Write to the temporary file
            content = stream.read()
            if isinstance(content, str):
                fh.write(content.encode("utf-8"))
            else:
                fh.write(content)
            fh.close()

            # Use puremagic to check for more extension options
            for g in self._guess_ext_magic(temp_path):
                self._append_ext(extensions, g)

            result = self._convert(temp_path, extensions, **kwargs)
        finally:
            try:
                fh.close()
            except Exception:
                pass
            os.unlink(temp_path)  # Delete the temporary file

        return result

    def _convert(self, local_path: str, extensions: list[str | None], **kwargs: Any) -> DocumentParseResult:
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")
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
                    res.text_content = "\n".join([line.rstrip() for line in re.split(r"\r?\n", res.text_content)])
                    res.text_content = re.sub(r"\n{3,}", "\n\n", res.text_content)
                    return res

        if len(error_trace) > 0:
            raise FileParseError(
                f"Could not convert '{local_path}' to Markdown. File type was recognized as {extensions}. While converting the file, the following error was encountered:\n\n{error_trace}"
            )

        raise FileTypeError(
            f"Could not convert '{local_path}' to Markdown. The formats {extensions} are not supported."
        )

    def convert(self, source: str | Path | BinaryIO | Any, **kwargs: Any) -> DocumentParseResult:
        # TODO: Add support for other source types
        if isinstance(source, str | Path):
            return self.convert_local(source, **kwargs)
        elif isinstance(source, BinaryIO):
            return self.convert_stream(source, **kwargs)
        else:
            raise ValueError(f"Unknown source type {type(source)}")

    def _append_ext(self, extensions: list[str], ext: str | None) -> None:
        """Append a unique non-None, non-empty extension to a list of extensions."""
        if ext is None:
            return
        ext = ext.strip()
        if ext == "":
            return
        if ext in extensions:
            return
        # if ext not in extensions:
        extensions.append(ext)

    def register_parser(self, parser: DocumentParser) -> None:
        """Register a document parser."""
        self.document_parsers.insert(0, parser)

    def _guess_ext_magic(self, path: str) -> list[str]:
        """Use puremagic (a Python implementation of libmagic) to guess a file's extension based on the first few bytes."""
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

            extensions = []
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
