"""
Phase 3 — Embedding pipeline

Reads every chunk file produced by Phase 2 (data/chunks/*_chunks.json),
embeds each chunk's text with the shared MiniLM embedder, and saves the
resulting vectors + full metadata to data/embeddings/chunk_embeddings.json.

This is a caching step: Phase 4 (vector store) reads this file rather than
re-embedding chunks every time, and re-running this script is idempotent
(it always regenerates the full file from the current chunks).
"""

import json
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import CHUNKS_DIR, EMBEDDINGS_DIR, FUND_SOURCES
from src.ingestion.embedder import embed_texts, MODEL_NAME

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("embed_chunks")


def load_all_chunks() -> list:
    """Load chunks from every scheme's chunk file produced by Phase 2."""
    all_chunks = []
    for source in FUND_SOURCES:
        chunk_path = CHUNKS_DIR / f"{source['slug']}_chunks.json"
        if not chunk_path.exists():
            logger.warning("Missing chunk file for %s, skipping. Run Phase 2 first.", source["slug"])
            continue
        with open(chunk_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        all_chunks.extend(chunks)
    return all_chunks


def save_embeddings(records: list) -> Path:
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EMBEDDINGS_DIR / "chunk_embeddings.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "model_name": MODEL_NAME,
                "chunk_count": len(records),
                "records": records,
            },
            f,
            ensure_ascii=False,
        )
    return out_path


def run() -> None:
    """Phase 3 entry point: embed all chunks from Phase 2 and cache the vectors."""
    logger.info("Starting Phase 3 — Embedding (model: %s)", MODEL_NAME)

    chunks = load_all_chunks()
    if not chunks:
        logger.error("No chunks found. Run Phase 1 and Phase 2 first.")
        return

    texts = [c["chunk_text"] for c in chunks]
    logger.info("Embedding %d chunks...", len(texts))
    vectors = embed_texts(texts)

    records = []
    for chunk, vector in zip(chunks, vectors):
        record = dict(chunk)  # keep all Phase 2 metadata: chunk_id, scheme_name, etc.
        record["embedding"] = vector
        records.append(record)

    out_path = save_embeddings(records)
    dim = len(records[0]["embedding"]) if records else 0
    logger.info(
        "Phase 3 complete: %d embeddings (dim=%d) saved -> %s",
        len(records), dim, out_path,
    )


if __name__ == "__main__":
    run()
