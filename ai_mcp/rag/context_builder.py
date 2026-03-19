# rag/context_builder.py

from typing import List, Dict


class ContextBuilder:
    """
    Builds a clean, deterministic, citation-safe context block
    from retrieved RAG chunks.
    Guarantees at least one chunk if retrieval is non-empty.
    """

    def __init__(self, max_chars: int = 2000):
        self.max_chars = max_chars

    def build_context(self, retrieved_chunks: List[Dict]) -> str:
        header = (
            "You are an assistant answering questions strictly using "
            "the context below.\n\n"
        )

        footer = (
            "\nIf the answer is not present in the context, respond with:\n"
            "\"I do not have that information.\""
        )

        context_parts = []
        current_length = len(header)
        seen_texts = set()

        for idx, chunk in enumerate(retrieved_chunks):
            text = chunk["text"].strip()

            if not text or text in seen_texts:
                continue

            seen_texts.add(text)

            block_header = (
                f"[Source: {chunk['source']} | Chunk: {chunk['chunk_id']}]\n"
            )

            available_space = self.max_chars - current_length - len(block_header)

            # 🚨 GUARANTEE: always include at least one chunk
            if available_space <= 0:
                break

            # Truncate text if needed
            if len(text) > available_space:
                text = text[:available_space].rstrip() + "..."

            block = f"{block_header}{text}\n\n"

            context_parts.append(block)
            current_length += len(block)

        context = header + "".join(context_parts) + footer
        return context
