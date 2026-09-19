"""
Phase 2 — Chunking

Reads each raw document from data/raw/<slug>.json and splits it into small,
fact-coherent chunks so a single fact (expense ratio, lock-in, etc.) is
never split across chunks — per architecture.md Phase 2.

Approach (since Groww's page text has no explicit section markers once
converted to plain text):
  1. Keyword-anchored chunking: for each known fact type (expense ratio,
     exit load, lock-in, minimum SIP, riskometer/benchmark, capital-gains
     statement), find lines mentioning it and take a small window of
     surrounding lines as one chunk. This keeps each fact type together.
  2. Overlapping windows for the same fact type are merged so we don't
     emit near-duplicate chunks.
  3. A fixed-size fallback pass ("general") covers any remaining content
     not captured by a fact keyword, so nothing on the page is lost to
     retrieval even if a question doesn't match a known fact type.

Every chunk carries: scheme_name, category, source_url, fetched_at,
fact_type, chunk_text, chunk_id.
"""

import json
import logging
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import RAW_DATA_DIR, CHUNKS_DIR, FUND_SOURCES

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("chunker")

# fact_type -> keyword patterns (case-insensitive) that anchor a chunk window
FACT_KEYWORD_PATTERNS = {
    "expense_ratio": [r"expense ratio"],
    "exit_load": [r"exit load"],
    "lock_in": [r"lock-in", r"lock in period", r"lockin"],
    "minimum_sip": [r"minimum sip", r"min\.?\s*sip", r"minimum investment", r"minimum lumpsum"],
    "riskometer_benchmark": [r"riskometer", r"risk-o-meter", r"risk factor", r"benchmark"],
    "capital_gains_statement": [r"capital gain", r"capital-gains statement", r"download statement"],
    "fund_overview": [r"fund manager", r"aum\b", r"nav\b", r"launch date", r"expense ratio.*category"],
}

# lines of context to include before/after a keyword match
LINES_BEFORE = 2
LINES_AFTER = 3

# fallback fixed-size chunking (characters) for content not caught by keywords
GENERAL_CHUNK_SIZE = 600
GENERAL_CHUNK_OVERLAP = 50


def find_keyword_windows(lines: list, patterns: list) -> list:
    """Return list of (start_idx, end_idx) windows around keyword matches."""
    windows = []
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    for i, line in enumerate(lines):
        if any(p.search(line) for p in compiled):
            start = max(0, i - LINES_BEFORE)
            end = min(len(lines), i + LINES_AFTER + 1)
            windows.append((start, end))
    return merge_overlapping_windows(windows)


def merge_overlapping_windows(windows: list) -> list:
    """Merge overlapping/adjacent (start, end) windows to avoid duplicate chunks."""
    if not windows:
        return []
    windows = sorted(windows)
    merged = [windows[0]]
    for start, end in windows[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def build_fact_chunks(lines: list) -> list:
    """
    For every fact_type, find its keyword windows and emit one chunk per
    window. Returns list of dicts: {fact_type, chunk_text, line_range}.
    """
    chunks = []
    covered_ranges = []

    for fact_type, patterns in FACT_KEYWORD_PATTERNS.items():
        windows = find_keyword_windows(lines, patterns)
        for start, end in windows:
            chunk_text = "\n".join(lines[start:end]).strip()
            if not chunk_text:
                continue
            chunks.append(
                {
                    "fact_type": fact_type,
                    "chunk_text": chunk_text,
                    "line_range": [start, end],
                }
            )
            covered_ranges.append((start, end))

    return chunks, merge_overlapping_windows(covered_ranges)


def build_general_chunks(lines: list, covered_ranges: list) -> list:
    """
    Fixed-size fallback chunking over the full text, tagged 'general', so
    content not caught by any fact keyword is still retrievable.
    """
    full_text = "\n".join(lines)
    chunks = []
    start_char = 0
    text_len = len(full_text)

    while start_char < text_len:
        end_char = min(start_char + GENERAL_CHUNK_SIZE, text_len)
        chunk_text = full_text[start_char:end_char].strip()
        if chunk_text:
            chunks.append({"fact_type": "general", "chunk_text": chunk_text})
        if end_char == text_len:
            break
        start_char = end_char - GENERAL_CHUNK_OVERLAP

    return chunks


def chunk_document(document: dict) -> list:
    """Chunk one scheme's raw document into a list of chunk dicts with metadata."""
    raw_text = document["raw_text"]
    lines = raw_text.splitlines()

    fact_chunks, covered_ranges = build_fact_chunks(lines)
    general_chunks = build_general_chunks(lines, covered_ranges)

    all_chunks = fact_chunks + general_chunks

    result = []
    for idx, chunk in enumerate(all_chunks):
        result.append(
            {
                "chunk_id": f"{document['category'].lower().replace(' ', '_')}_{chunk['fact_type']}_{idx}",
                "scheme_name": document["scheme_name"],
                "category": document["category"],
                "source_url": document["source_url"],
                "fetched_at": document["fetched_at"],
                "fact_type": chunk["fact_type"],
                "chunk_text": chunk["chunk_text"],
            }
        )
    return result


def save_chunks(chunks: list, slug: str) -> Path:
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CHUNKS_DIR / f"{slug}_chunks.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    return out_path


def run() -> None:
    """Phase 2 entry point: chunk every raw document produced by Phase 1."""
    logger.info("Starting Phase 2 — Chunking for %d sources", len(FUND_SOURCES))
    total_chunks = 0

    for source in FUND_SOURCES:
        raw_path = RAW_DATA_DIR / f"{source['slug']}.json"
        if not raw_path.exists():
            logger.warning("Missing raw file for %s, skipping. Run Phase 1 first.", source["slug"])
            continue

        with open(raw_path, "r", encoding="utf-8") as f:
            document = json.load(f)

        chunks = chunk_document(document)
        out_path = save_chunks(chunks, source["slug"])

        fact_types_found = sorted({c["fact_type"] for c in chunks if c["fact_type"] != "general"})
        logger.info(
            "%s: %d chunks saved -> %s (fact types found: %s)",
            source["slug"], len(chunks), out_path, fact_types_found or "none",
        )
        total_chunks += len(chunks)

    logger.info("Phase 2 complete: %d total chunks written across all sources", total_chunks)


if __name__ == "__main__":
    run()
