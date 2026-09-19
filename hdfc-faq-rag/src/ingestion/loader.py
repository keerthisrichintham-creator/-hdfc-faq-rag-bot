"""
Phase 1 — Data Loading

Fetches the 5 approved Groww Direct Growth pages (only) and saves a cleaned
raw text snapshot + metadata for each scheme to data/raw/<slug>.json.

This module does NOT chunk or interpret the content — that is Phase 2.
Its only job is: fetch -> clean -> save, for exactly the 5 configured URLs.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
from src.config import (
    FUND_SOURCES,
    RAW_DATA_DIR,
    REQUEST_HEADERS,
    REQUEST_TIMEOUT_SECONDS,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("loader")


def fetch_html(url: str) -> str:
    """Fetch raw HTML for a single URL. Raises on non-200 responses."""
    response = requests.get(
        url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT_SECONDS
    )
    response.raise_for_status()
    return response.text


def clean_text_from_html(html: str) -> str:
    """
    Strip script/style/nav/footer noise and collapse whitespace,
    returning the readable body text of the page.
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    non_empty_lines = [line for line in lines if line]
    cleaned = "\n".join(non_empty_lines)
    return cleaned


def load_one(source: dict) -> dict:
    """Fetch + clean one scheme's page, return a document dict."""
    logger.info("Fetching: %s (%s)", source["scheme_name"], source["url"])
    html = fetch_html(source["url"])
    text = clean_text_from_html(html)

    document = {
        "scheme_name": source["scheme_name"],
        "category": source["category"],
        "source_url": source["url"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "raw_text": text,
    }
    return document


def save_document(document: dict, slug: str) -> Path:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAW_DATA_DIR / f"{slug}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, indent=2)
    return out_path


def run() -> None:
    """Phase 1 entry point: load all 5 configured sources, nothing else."""
    logger.info("Starting Phase 1 — Data Loading for %d sources", len(FUND_SOURCES))
    results = []

    for source in FUND_SOURCES:
        try:
            document = load_one(source)
            out_path = save_document(document, source["slug"])
            char_count = len(document["raw_text"])
            logger.info(
                "Saved %s -> %s (%d chars)", source["slug"], out_path, char_count
            )
            results.append({"slug": source["slug"], "status": "ok", "chars": char_count})
        except Exception as exc:
            logger.error("Failed to load %s: %s", source["slug"], exc)
            results.append({"slug": source["slug"], "status": "failed", "error": str(exc)})

    ok_count = sum(1 for r in results if r["status"] == "ok")
    logger.info("Phase 1 complete: %d/%d sources loaded successfully", ok_count, len(FUND_SOURCES))

    failed = [r for r in results if r["status"] != "ok"]
    if failed:
        logger.warning(
            "Some sources failed — this can happen if Groww renders content "
            "client-side via JavaScript. See README for the Playwright fallback."
        )
        for r in failed:
            logger.warning("  %s: %s", r["slug"], r.get("error"))


if __name__ == "__main__":
    run()
