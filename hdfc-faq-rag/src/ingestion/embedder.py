"""
Phase 3 — Embedding (shared module)

Wraps sentence-transformers/all-MiniLM-L6-v2 so that ingestion-time chunk
embedding and query-time embedding always use the exact same model and
settings — per architecture.md ("same" embedding step in both pipelines).

This module has no side effects on import; the model is loaded lazily on
first use so importing it (e.g., from the Streamlit app) is cheap.
"""

import logging
from typing import List

logger = logging.getLogger("embedder")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None  # lazy singleton


def get_model():
    """Load (once) and return the shared SentenceTransformer model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", MODEL_NAME)
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: List[str], batch_size: int = 32) -> List[List[float]]:
    """
    Embed a batch of texts (used for chunks at ingestion time).
    Returns a list of embedding vectors (list of floats), same order as input.
    """
    if not texts:
        return []
    model = get_model()
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,  # cosine similarity via dot product
    )
    return vectors.tolist()


def embed_query(text: str) -> List[float]:
    """
    Embed a single user query (used at retrieval time).
    Uses the exact same model/settings as embed_texts for consistency.
    """
    return embed_texts([text])[0]
