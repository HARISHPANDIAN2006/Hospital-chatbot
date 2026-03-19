# vector_store/store.py

import json
from pathlib import Path
from typing import List, Dict


class LocalVectorStore:
    def __init__(self, embeddings_path: Path, chunks_path: Path):
        self.embeddings = self._load_json(embeddings_path)
        self.chunks = {c["chunk_id"]: c for c in self._load_json(chunks_path)}

    @staticmethod
    def _load_json(path: Path) -> List[Dict]:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_all_vectors(self) -> List[Dict]:
        return self.embeddings

    def get_chunk_text(self, chunk_id: str) -> str:
        return self.chunks[chunk_id]["text"]

    def get_chunk_source(self, chunk_id: str) -> str:
        return self.chunks[chunk_id]["source"]
