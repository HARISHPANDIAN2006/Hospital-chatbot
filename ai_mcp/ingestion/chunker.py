# ingestion/chunker.py

from typing import List, Dict
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP

def _split_words(text: str) -> List[str]:
    """Split text into words deterministically."""
    return text.split()


def chunk_document(document: Dict) -> List[Dict]:
    """
    Split a single document into fixed-size chunks.

    Returns:
        List of Chunk dictionaries
    """
    words = _split_words(document["text"])
    chunks = []

    start = 0
    chunk_index = 0

    while start < len(words):
        end = start + CHUNK_SIZE
        chunk_words = words[start:end]

        chunk_text = " ".join(chunk_words)

        chunk = {
            "chunk_id": f"{document['doc_id']}_chunk_{chunk_index:03d}",
            "text": chunk_text,
            "parent_doc": document["doc_id"],
            "chunk_index": chunk_index,
            "source": document["source"]
        }

        chunks.append(chunk)

        start += CHUNK_SIZE - CHUNK_OVERLAP
        chunk_index += 1

    return chunks


def chunk_documents(documents: List[Dict]) -> List[Dict]:
    """Chunk all documents."""
    all_chunks = []

    for document in documents:
        all_chunks.extend(chunk_document(document))

    return all_chunks
