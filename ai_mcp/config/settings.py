# config/settings.py

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DOCS_PATH = BASE_DIR / "data" / "raw_docs"
PROCESSED_DOCS_PATH = BASE_DIR / "data" / "processed_docs"

# Chunking configuration
CHUNK_SIZE = 300        # number of words per chunk
CHUNK_OVERLAP = 50      # overlapping words between chunks

# Supported file types
SUPPORTED_EXTENSIONS = {".txt", ".md", ".csv"}
