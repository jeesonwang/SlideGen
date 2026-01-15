from __future__ import annotations

import os
import uuid
from pathlib import Path

import aiohttp
from loguru import logger


async def download_file(url: str, output_directory: str) -> str:
    """download file from URL and save to specified directory, return saved path.

    - use aiohttp to download asynchronously
    - if directory does not exist, create it
    - file name uses uuid, preserves original extension (if any)
    """
    try:
        Path(output_directory).mkdir(parents=True, exist_ok=True)

        suffix = Path(url).suffix or ".jpg"
        filename = f"{uuid.uuid4()}{suffix}"
        filepath = os.path.join(output_directory, filename)

        async with aiohttp.ClientSession(trust_env=True) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                content = await resp.read()

        with open(filepath, "wb") as f:
            f.write(content)

        logger.info(f"Download completed: {url} -> {filepath}")
        return filepath
    except Exception:
        logger.exception(f"Download failed: {url}")
        raise
