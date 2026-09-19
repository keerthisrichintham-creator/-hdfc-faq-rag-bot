"""
Central config for the RAG prototype.
Scope lock: ONLY these 5 URLs are ever fetched, anywhere in the pipeline.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
EMBEDDINGS_DIR = PROJECT_ROOT / "data" / "embeddings"
VECTOR_DB_DIR = PROJECT_ROOT / "data" / "vector_db" / "chroma"

# The 5 approved sources — do not add to this list without updating the PRD.
FUND_SOURCES = [
    {
        "category": "Large Cap",
        "scheme_name": "HDFC Large Cap Fund",
        "slug": "hdfc_large_cap",
        "url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    },
    {
        "category": "Flexi Cap",
        "scheme_name": "HDFC Flexi Cap Fund",
        "slug": "hdfc_flexi_cap",
        "url": "https://groww.in/mutual-funds/hdfc-flexi-cap-fund-direct-growth",
    },
    {
        "category": "ELSS",
        "scheme_name": "HDFC ELSS Tax Saver Fund",
        "slug": "hdfc_elss_tax_saver",
        "url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-growth",
    },
    {
        "category": "Mid Cap",
        "scheme_name": "HDFC Mid Cap Opportunities Fund",
        "slug": "hdfc_mid_cap_opportunities",
        "url": "https://groww.in/mutual-funds/hdfc-mid-cap-opportunities-fund-direct-growth",
    },
    {
        "category": "Small Cap",
        "scheme_name": "HDFC Small Cap Fund",
        "slug": "hdfc_small_cap",
        "url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    },
]

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT_SECONDS = 20
