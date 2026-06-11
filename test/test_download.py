"""test slidegen.utils.download"""

from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slidegen.utils.download import download_file


def _patched_session(payload: bytes = b"\xff\xd8\xff\xe0fake-jpeg"):
    """build a context-manager mock that mimics aiohttp.ClientSession.get(...)."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.read = AsyncMock(return_value=payload)

    get_ctx = MagicMock()
    get_ctx.__aenter__ = AsyncMock(return_value=resp)
    get_ctx.__aexit__ = AsyncMock(return_value=None)

    session = MagicMock()
    session.get = MagicMock(return_value=get_ctx)

    session_ctx = MagicMock()
    session_ctx.__aenter__ = AsyncMock(return_value=session)
    session_ctx.__aexit__ = AsyncMock(return_value=None)

    return session_ctx


class TestDownloadFile:
    """download_file extension-handling regressions"""

    @pytest.mark.anyio
    async def test_query_string_is_stripped_from_extension(self, tmp_path):
        """URL with query string should not leak `?...` into the saved filename.

        Pexels returns URLs like `.../foo.jpeg?auto=compress&cs=tinysrgb` —
        a naive `Path(url).suffix` keeps the whole `.jpeg?...` as the suffix
        and produces a filename containing `?`, which breaks downstream
        consumers that treat the path as a plain file path.
        """
        url = "https://images.pexels.com/photos/1/foo.jpeg?auto=compress&cs=tinysrgb&h=650&w=940"

        with patch("slidegen.utils.download.aiohttp.ClientSession", return_value=_patched_session()):
            saved = await download_file(url, str(tmp_path))

        assert os.path.exists(saved)
        basename = os.path.basename(saved)
        assert "?" not in basename
        assert "&" not in basename
        assert basename.endswith(".jpeg")

    @pytest.mark.anyio
    async def test_url_without_extension_falls_back_to_jpg(self, tmp_path):
        url = "https://example.com/api/image"

        with patch("slidegen.utils.download.aiohttp.ClientSession", return_value=_patched_session()):
            saved = await download_file(url, str(tmp_path))

        assert os.path.basename(saved).endswith(".jpg")

    @pytest.mark.anyio
    async def test_plain_url_keeps_extension(self, tmp_path):
        url = "https://example.com/pic.png"

        with patch("slidegen.utils.download.aiohttp.ClientSession", return_value=_patched_session()):
            saved = await download_file(url, str(tmp_path))

        assert os.path.basename(saved).endswith(".png")
