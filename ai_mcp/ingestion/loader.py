# ingestion/loader.py

from pathlib import Path
from typing import List, Dict
from config.settings import SUPPORTED_EXTENSIONS
import csv

def _read_file(file_path: Path) -> str:
    if file_path.suffix == ".csv":
        rows = []
        with open(file_path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(" | ".join(row))
        return "\n".join(rows)
    else:
        return file_path.read_text(encoding="utf-8").strip()

def load_documents(raw_docs_path: Path) -> List[Dict]:
    """
    Load raw documents from disk and attach metadata.

    Returns:
        List of Document dictionaries
    """
    documents = []

    files = sorted(
        [f for f in raw_docs_path.iterdir() if f.suffix in SUPPORTED_EXTENSIONS]
    )

    for idx, file_path in enumerate(files):
        text = _read_file(file_path)

        document = {
            "doc_id": f"doc_{idx:03d}",
            "text": text,
            "source": file_path.name,
            "domain": "admin"  # static for Phase 1
        }

        documents.append(document)

    return documents
