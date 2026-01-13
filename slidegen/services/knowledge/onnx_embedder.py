import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from agno.knowledge.embedder.base import Embedder
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from loguru import logger

from slidegen.core.config import settings


@dataclass
class ONNXEmbedder(Embedder):
    """
    Custom ONNX embedder for agno framework using chromadb's ONNXMiniLM_L6_V2.
    This embedder uses a local ONNX model for offline embedding generation.
    """

    dimensions: int = 384
    model_path: Path = field(default_factory=lambda: settings.CHROMA_MODELS_PATH)
    _onnx_function: ONNXMiniLM_L6_V2 | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the ONNX embedding function."""
        if self._onnx_function is None:
            logger.info("Initializing ONNX embedder with local model...")
            self._onnx_function = ONNXMiniLM_L6_V2()
            self._onnx_function.DOWNLOAD_PATH = self.model_path
            self._onnx_function._download_model_if_not_exists()
            logger.info("ONNX embedder initialized successfully")

    def get_embedding(self, text: str) -> list[float]:
        """
        Get embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            List of embedding values
        """
        if self._onnx_function is None:
            self.__post_init__()

        try:
            # ONNXMiniLM_L6_V2 expects a list of texts and returns a list of embeddings
            embeddings = self._onnx_function([text])  # type: ignore
            if embeddings:
                return cast(list[float], embeddings[0].tolist())
            return []
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []

    def get_embedding_and_usage(self, text: str) -> tuple[list[float], dict[str, Any] | None]:
        """
        Get embedding and usage info. ONNX models don't track usage, so usage is None.

        Args:
            text: Text to embed

        Returns:
            Tuple of (embedding, None)
        """
        return self.get_embedding(text=text), None

    async def async_get_embedding(self, text: str) -> list[float]:
        """
        Async version using thread executor for CPU-bound operations.

        Args:
            text: Text to embed

        Returns:
            List of embedding values
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_embedding, text)

    async def async_get_embedding_and_usage(self, text: str) -> tuple[list[float], dict[str, Any] | None]:
        """
        Async version with usage info. ONNX models don't track usage, so usage is None.

        Args:
            text: Text to embed

        Returns:
            Tuple of (embedding, None)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_embedding_and_usage, text)
