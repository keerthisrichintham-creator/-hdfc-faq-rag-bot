"""
Phase 4 — Vector Store

Loads the cached embeddings + metadata produced by Phase 3
(data/embeddings/chunk_embeddings.json) and persists them into a local
ChromaDB collection at data/vector_db/chroma, per architecture.md.

Uses collection.upsert() (not add()) keyed on chunk_id, so re-running this
script after a re-ingestion does NOT create duplicate records — it just
overwrites the existing ones.

This module does not re-embed anything and does not touch data/raw or
data/chunks — it only reads the already-computed embeddings file.
"""

import json
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import EMBEDDINGS_DIR, VECTOR_DB_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("vector_store")

COLLECTION_NAME = "hdfc_fund_chunks"
UPSERT_BATCH_SIZE = 200

_client = None  # lazy singleton, so retriever.py can share one connection


def get_client():
    """Return a persistent ChromaDB client backed by data/vector_db/chroma."""
    global _client
    if _client is None:
        import chromadb

        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Opening ChromaDB persistent store at %s", VECTOR_DB_DIR)
        _client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    return _client


def get_collection():
    """
    Return the shared collection, creating it if needed.
    Cosine space matches the normalized embeddings produced in Phase 3.
    """
    client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_embeddings_file() -> tuple:
    """Load Phase 3's cached embeddings file. Raises if it doesn't exist."""
    path = EMBEDDINGS_DIR / "chunk_embeddings.json"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run Phase 3 (src/ingestion/embed_chunks.py) first."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["records"], data.get("model_name", "unknown")


def build_chroma_payload(records: list) -> tuple:
    """
    Convert Phase 3 records into the parallel lists ChromaDB expects:
    ids, embeddings, documents (the chunk text), and metadatas.
    """
    ids, embeddings, documents, metadatas = [], [], [], []
    for r in records:
        ids.append(r["chunk_id"])
        embeddings.append(r["embedding"])
        documents.append(r["chunk_text"])
        metadatas.append(
            {
                "scheme_name": r["scheme_name"],
                "category": r["category"],
                "source_url": r["source_url"],
                "fetched_at": r["fetched_at"],
                "fact_type": r["fact_type"],
            }
        )
    return ids, embeddings, documents, metadatas


def upsert_in_batches(collection, ids, embeddings, documents, metadatas, batch_size=UPSERT_BATCH_SIZE):
    total = len(ids)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        collection.upsert(
            ids=ids[start:end],
            embeddings=embeddings[start:end],
            documents=documents[start:end],
            metadatas=metadatas[start:end],
        )
        logger.info("Upserted batch %d-%d of %d", start, end, total)


def run() -> None:
    """Phase 4 entry point: load Phase 3 embeddings, persist them to ChromaDB."""
    logger.info("Starting Phase 4 — Vector Store")

    records, model_name = load_embeddings_file()
    logger.info("Loaded %d embedded chunks (model: %s)", len(records), model_name)

    ids, embeddings, documents, metadatas = build_chroma_payload(records)

    collection = get_collection()
    upsert_in_batches(collection, ids, embeddings, documents, metadatas)

    final_count = collection.count()
    logger.info(
        "Phase 4 complete: collection '%s' has %d records (expected %d)",
        COLLECTION_NAME, final_count, len(ids),
    )

    # Quick per-category sanity breakdown
    categories = sorted({m["category"] for m in metadatas})
    for category in categories:
        cat_count = sum(1 for m in metadatas if m["category"] == category)
        logger.info("  %s: %d chunks", category, cat_count)

    if final_count != len(ids):
        logger.warning(
            "Stored count (%d) does not match input count (%d) — "
            "check for duplicate chunk_ids in Phase 2 output.",
            final_count, len(ids),
        )


if __name__ == "__main__":
    run()
