# rag/retriever.py

from typing import List, Dict
from vector_store.similarity import cosine_similarity
from embeddings.embedder import LocalEmbedder


class Retriever:
    def __init__(self, vector_store, embedder: LocalEmbedder):
        self.vector_store = vector_store
        self.embedder = embedder

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        query_vector = self.embedder.embed([query])[0]

        scored_chunks = []

        for entry in self.vector_store.get_all_vectors():
            score = cosine_similarity(query_vector, entry["embedding"])

            scored_chunks.append({
                "chunk_id": entry["chunk_id"],
                "score": score
            })

        scored_chunks.sort(key=lambda x: x["score"], reverse=True)

        results = []
        for item in scored_chunks[:top_k]:
            results.append({
                "chunk_id": item["chunk_id"],
                "score": round(item["score"], 4),
                "text": self.vector_store.get_chunk_text(item["chunk_id"]),
                "source": self.vector_store.get_chunk_source(item["chunk_id"])
            })

        return results
