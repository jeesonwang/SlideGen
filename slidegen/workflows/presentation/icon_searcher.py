import asyncio
import json
from pathlib import Path

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
from loguru import logger


class IconSearcher:
    def __init__(self) -> None:
        self.collection_name = "icons"
        self.client = chromadb.PersistentClient(path="chroma", settings=Settings(anonymized_telemetry=False))
        logger.info("Initializing icons collection...")
        self._initialize_icons_collection()
        logger.info("Icons collection initialized.")
        self.default_icons_path = Path("components/icons.json")

    def _initialize_icons_collection(self) -> None:
        self.embedding_function = ONNXMiniLM_L6_V2()
        self.embedding_function.DOWNLOAD_PATH = Path("chroma/models")
        self.embedding_function._download_model_if_not_exists()
        try:
            self.collection = self.client.get_collection(
                self.collection_name,
                embedding_function=self.embedding_function,  # type: ignore[arg-type]
            )
        except Exception:
            with open(self.default_icons_path) as f:
                icons = json.load(f)

            documents = []
            ids = []

            for each in icons["icons"]:
                if each["name"].split("-")[-1] == "bold":
                    doc_text = f"{each['name']} {each['tags']}"
                    documents.append(doc_text)
                    ids.append(each["name"])

            if documents:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function,  # type: ignore[arg-type]
                    metadata={"hnsw:space": "cosine"},
                )
                self.collection.add(documents=documents, ids=ids)

    async def search_icons(self, query: str, k: int = 1) -> list[str]:
        result = await asyncio.to_thread(
            self.collection.query,
            query_texts=[query],
            n_results=k,
        )
        return [f"components/icons/bold/{each}.png" for each in result["ids"][0]]


icon_searcher = IconSearcher()
