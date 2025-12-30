import uuid
from pathlib import Path
from typing import Any

from agno.knowledge.embedder.base import Embedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb
from loguru import logger


class KnowledgeBaseManager:
    """Knowledge Base Manager, using agno.knowledge.Knowledge"""

    def __init__(self, user_id: str, session_id: str | None = None, embedder: Embedder | None = None):
        """
        Initialize the knowledge base manager

        Args:
            user_id: User ID, for isolating user data
            session_id: Session ID, for distinguishing different PPT generation tasks. If None, it will be automatically generated
            embedder: Embedder instance, if None, will use default OpenAI embedder from environment variables (for backward compatibility)
        """
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())

        # Create collection name: user_{user_id}_session_{session_id}
        self.collection_name = f"user_{user_id}_{self.session_id}"

        # Set ChromaDB path
        chroma_path = Path("chroma") / "knowledge"
        chroma_path.mkdir(parents=True, exist_ok=True)

        # Use provided embedder or default
        if embedder:
            logger.info(f"Using provided embedder: {type(embedder).__name__}")
        else:
            logger.warning("No embedder provided, will use default OpenAI embedder from environment variables")

        # Initialize ChromaDB vector database
        self.vector_db = ChromaDb(
            collection=self.collection_name,
            path=str(chroma_path),
            persistent_client=True,
            embedder=embedder,
        )

        # Initialize Knowledge
        self.knowledge = Knowledge(
            vector_db=self.vector_db,
            max_results=5,  # add 5 knowledge base knowledge to the context each time
        )

        logger.info(f"Initialized KnowledgeBaseManager for user {user_id}, session {self.session_id}")

    async def add_document(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """
        Add a single document to the knowledge base

        Args:
            content: Document content
            metadata: Metadata (e.g. filename, source, etc.)
        """
        try:
            # Use agno's add_content_async to add content
            # Note: agno will automatically chunk and vectorize
            await self.knowledge.add_content_async(
                text_content=content,
                metadata=metadata,
            )
            logger.info(
                f"Added document to knowledge base: {metadata.get('source', 'unknown') if metadata else 'unknown'}"
            )
        except Exception as e:
            logger.error(f"Failed to add document to knowledge base: {e}")
            raise

    async def add_documents(self, documents: list[str], metadata_list: list[dict[str, Any]] | None = None) -> None:
        """
        Add multiple documents to the knowledge base

        Args:
            documents: List of document contents
            metadata_list: List of metadata, corresponding to documents
        """
        if metadata_list is None:
            metadata_list = [{}] * len(documents)

        if len(documents) != len(metadata_list):
            raise ValueError("documents and metadata_list must have the same length")

        for doc, meta in zip(documents, metadata_list, strict=False):
            await self.add_document(doc, meta)

        logger.info(f"Added {len(documents)} documents to knowledge base")

    async def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Search for relevant document fragments

        Args:
            query: Query text
            limit: Number of results to return

        Returns:
            List of relevant document fragments, each containing content and metadata
        """
        try:
            # Use vector_db directly to search
            results = await self.vector_db.async_search(
                query=query,
                limit=limit,
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "content": result.content,
                        "metadata": result.meta_data,
                        "distance": result.reranking_score,
                    }
                )

            logger.debug(f"Found {len(formatted_results)} relevant documents for query: {query[:50]}...")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search knowledge base: {e}")
            return []

    async def clear(self) -> None:
        """Clear the knowledge base for the current session"""
        try:
            # Delete collection
            self.vector_db.delete()
            logger.info(f"Cleared knowledge base for session {self.session_id}")
        except Exception as e:
            logger.error(f"Failed to clear knowledge base: {e}")
            raise

    def get_stats(self) -> dict[str, Any]:
        """
        Get knowledge base statistics

        Returns:
            Dictionary containing statistics
        """
        try:
            collection_stats = {
                "user_id": self.user_id,
                "session_id": self.session_id,
                "collection_name": self.collection_name,
            }
            return collection_stats
        except Exception as e:
            logger.error(f"Failed to get knowledge base stats: {e}")
            return {}
