import json

from agno.vectordb.chroma import ChromaDb
from loguru import logger

from slidegen.core.config import settings
from slidegen.services.knowledge.onnx_embedder import ONNXEmbedder


class IconSearcher:
    """Icon searcher using agno framework with local ONNX embeddings"""

    def __init__(self) -> None:
        self.collection_name = "icons"
        self.default_icons_path = settings.ICONS_JSON_PATH

        logger.info("Initializing ONNX embedder for icons...")
        self.embedder = ONNXEmbedder(model_path=settings.CHROMA_MODELS_PATH)

        logger.info("Initializing icons vector database...")
        self._initialize_vector_db()
        logger.info("Icons collection initialized.")

    def _initialize_vector_db(self) -> None:
        """Initialize ChromaDB vector database using agno framework"""
        chroma_path = settings.CHROMA_BASE_PATH
        chroma_path.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB with agno
        self.vector_db = ChromaDb(
            collection=self.collection_name,
            path=str(chroma_path),
            persistent_client=True,
            embedder=self.embedder,
        )

        # Check if collection needs to be populated
        if not self._is_collection_populated():
            logger.info("Icons collection is empty, populating from icons.json...")
            self._populate_icons()

    def _is_collection_populated(self) -> bool:
        """Check if the icons collection has any data"""
        try:
            # Access the internal ChromaDB client to check collection count
            # This is a workaround since agno doesn't expose a count method
            if hasattr(self.vector_db, "client") and hasattr(self.vector_db.client, "get_collection"):
                try:
                    collection = self.vector_db.client.get_collection(name=self.collection_name)
                    count = collection.count()
                    logger.debug(f"Icons collection has {count} documents")
                    return count > 0
                except Exception as e:
                    logger.debug(f"Collection not found or error checking count: {e}")
                    return False
            return False
        except Exception as e:
            logger.debug(f"Error checking if collection is populated: {e}")
            return False

    def _populate_icons(self) -> None:
        """Populate the icons collection from icons.json"""
        try:
            with open(self.default_icons_path) as f:
                icons_data = json.load(f)

            documents: list[str] = []
            metadatas: list[dict[str, str]] = []
            ids: list[str] = []

            for icon in icons_data["icons"]:
                # Only include "bold" icons
                if icon["name"].split("-")[-1] == "bold":
                    doc_text = f"{icon['name']} {icon['tags']}"
                    documents.append(doc_text)
                    metadatas.append(
                        {
                            "name": str(icon["name"]),
                            "tags": str(icon["tags"]),
                        }
                    )
                    ids.append(str(icon["name"]))

            if documents:
                logger.info(f"Adding {len(documents)} icons to the collection...")
                # Use the underlying ChromaDB collection directly for batch insert
                # This is more efficient and matches the original implementation
                if hasattr(self.vector_db, "_collection") and self.vector_db._collection is not None:
                    self.vector_db._collection.add(
                        documents=documents,
                        metadatas=metadatas,  # type: ignore
                        ids=ids,
                    )
                    logger.info("Icons successfully added to the collection")
                else:
                    logger.error("ChromaDB collection not initialized")
                    raise RuntimeError("ChromaDB collection not initialized")

        except Exception as e:
            logger.error(f"Failed to populate icons collection: {e}")
            raise

    async def search_icons(self, query: str, k: int = 1) -> list[str]:
        """
        Search for icons matching the query.

        Args:
            query: Search query text
            k: Number of results to return

        Returns:
            List of icon file paths
        """
        try:
            # Use agno's async_search method
            results = await self.vector_db.async_search(
                query=query,
                limit=k,
            )

            # Extract icon names from results and format as file paths
            icon_paths = []
            for result in results:
                # Get icon name from the document ID
                # The ID is set to the icon name when we populate the collection
                icon_name = result.id if hasattr(result, "id") else None
                if icon_name:
                    icon_paths.append(str(settings.ICONS_DIR / f"{icon_name}.png"))
                    logger.debug(f"Found icon: {icon_name} (distance: {result.meta_data.get('distances', 'N/A')})")
                else:
                    logger.warning(f"No icon ID in result: {result}")

            return icon_paths

        except Exception as e:
            logger.error(f"Failed to search icons: {e}")
            return []


icon_searcher = IconSearcher()
