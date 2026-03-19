# embeddings/embedder.py

import pickle
from typing import List
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer


class LocalEmbedder:
    """
    Deterministic local embedding engine using TF-IDF.

    IMPORTANT:
    - The same fitted vectorizer MUST be reused for retrieval.
    - Therefore, we persist and reload the vectorizer from disk.
    """

    def __init__(self):
        self.vectorizer: TfidfVectorizer | None = None

    # -----------------------------
    # FITTING (PHASE 2 ONLY)
    # -----------------------------
    def fit(self, texts: List[str]) -> None:
        """
        Fit the TF-IDF vectorizer on the corpus.
        Should be called ONLY during Phase 2.
        """
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english"
        )
        self.vectorizer.fit(texts)

    # -----------------------------
    # EMBEDDING (PHASE 2 & 3)
    # -----------------------------
    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Convert text into embeddings using the fitted vectorizer.
        """
        if self.vectorizer is None:
            raise RuntimeError(
                "Vectorizer is not loaded or fitted. "
                "Call fit() or load() before embed()."
            )

        vectors = self.vectorizer.transform(texts)
        return vectors.toarray().tolist()

    # -----------------------------
    # PERSISTENCE (CRITICAL)
    # -----------------------------
    def save(self, path: Path) -> None:
        """
        Save the fitted vectorizer to disk.
        """
        if self.vectorizer is None:
            raise RuntimeError("No vectorizer to save.")

        with open(path, "wb") as f:
            pickle.dump(self.vectorizer, f)

    def load(self, path: Path) -> None:
        """
        Load a previously fitted vectorizer from disk.
        """
        if not path.exists():
            raise FileNotFoundError(
                f"Vectorizer file not found at: {path}"
            )

        with open(path, "rb") as f:
            self.vectorizer = pickle.load(f)
