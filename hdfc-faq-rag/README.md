# HDFC Mutual Fund FAQ Assistant — Phase 1: Data Loading

Steps to run Phase 1 (Data Loading) on your terminal.

## 1. Open the project folder
```bash
cd hdfc-faq-rag
```

## 2. Create and activate a virtual environment
```bash
python3 -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

## 3. Install dependencies
```bash
pip install -r requirements.txt
```

## 4. Run the Phase 1 loader
```bash
python -m src.ingestion.loader
```

## 5. Verify the output
```bash
ls data/raw
```
You should see 5 files:
```
hdfc_large_cap.json
hdfc_flexi_cap.json
hdfc_elss_tax_saver.json
hdfc_mid_cap_opportunities.json
hdfc_small_cap.json
```

Each file contains:
```json
{
  "scheme_name": "HDFC Large Cap Fund",
  "category": "Large Cap",
  "source_url": "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
  "fetched_at": "2026-09-04T12:00:00+00:00",
  "raw_text": "... cleaned page text ..."
}
```

Spot-check one file to confirm expense ratio / lock-in / exit load / riskometer
text actually appears in `raw_text`:
```bash
cat data/raw/hdfc_large_cap.json | head -c 1000
```

## Troubleshooting

**A file's `raw_text` looks empty or missing key numbers.**
Groww's pages may render some data client-side via JavaScript, which a plain
`requests` fetch won't execute. If that happens:
1. `pip install playwright && playwright install chromium`
2. Swap `fetch_html()` in `src/ingestion/loader.py` for a Playwright-based
   fetch (load the page, wait for network idle, then grab `page.content()`).
   Everything downstream (`clean_text_from_html`, saving, metadata) stays
   the same — only the fetch step changes.

**Getting a 403 / blocked response.**
Check `REQUEST_HEADERS` in `src/config.py` — try adding `Accept-Language`
and `Referer` headers, or slow down requests (add a short `time.sleep()`
between fetches) if you're hitting rate limits.

## Next phase
Once all 5 `data/raw/*.json` files look correct, you're ready for
**Phase 2 — Chunking** (`src/ingestion/chunker.py`), per `docs/architecture.md`.

---

# Phase 2: Chunking

Splits each raw document into small, fact-coherent chunks (expense ratio,
exit load, lock-in, minimum SIP, riskometer/benchmark, capital-gains
statement, fund overview), plus a fixed-size "general" fallback pass so no
page content is lost even if it doesn't match a known fact keyword.

## 1. Run the chunker (after Phase 1 has produced `data/raw/*.json`)
```bash
python -m src.ingestion.chunker
```

## 2. Verify the output
```bash
ls data/chunks
```
You should see 5 files, one per scheme:
```
hdfc_large_cap_chunks.json
hdfc_flexi_cap_chunks.json
hdfc_elss_tax_saver_chunks.json
hdfc_mid_cap_opportunities_chunks.json
hdfc_small_cap_chunks.json
```

Check that the key fact types were actually found for a scheme:
```bash
python3 -c "
import json
chunks = json.load(open('data/chunks/hdfc_large_cap_chunks.json'))
print(sorted({c['fact_type'] for c in chunks}))
"
```
Expect to see `expense_ratio`, `exit_load`, `lock_in`, `minimum_sip`,
`riskometer_benchmark` in that list (plus `general` and possibly
`capital_gains_statement` / `fund_overview` if present on the page).

## Troubleshooting

**A fact type is missing from the list (e.g., no `lock_in` chunk).**
Open `data/raw/<slug>.json` and search for how that fact is actually worded
on the live page — Groww's wording can differ slightly (e.g., "Lock in"
vs "Lock-in Period"). Add the exact phrase as a new pattern to
`FACT_KEYWORD_PATTERNS` in `src/ingestion/chunker.py` and re-run.

**Chunks look too short or cut off mid-fact.**
Increase `LINES_BEFORE` / `LINES_AFTER` in `src/ingestion/chunker.py` to
widen the context window around each keyword match.

## Next phase
Once all 5 `data/chunks/*_chunks.json` files look correct and contain the
expected fact types, you're ready for **Phase 3 — Embedding**
(`src/ingestion/embedder.py`), per `docs/architecture.md`.

---

# Phase 3: Embedding

Embeds every chunk from Phase 2 using `sentence-transformers/all-MiniLM-L6-v2`
and caches the vectors + metadata to `data/embeddings/chunk_embeddings.json`.
The same `embedder.py` module will be reused at query time in Phase 5, so
ingestion and retrieval never drift out of sync on embedding logic.

## 1. Install dependencies (adds sentence-transformers + numpy)
```bash
pip install -r requirements.txt
```
> First run will also download the MiniLM model (~90MB) from Hugging Face —
> make sure you have internet access the first time you run this.

## 2. Run the embedding pipeline (after Phase 2 has produced `data/chunks/*.json`)
```bash
python -m src.ingestion.embed_chunks
```

## 3. Verify the output
```bash
python3 -c "
import json
data = json.load(open('data/embeddings/chunk_embeddings.json'))
print('model:', data['model_name'])
print('chunk_count:', data['chunk_count'])
print('embedding dim:', len(data['records'][0]['embedding']))
print('sample chunk_id:', data['records'][0]['chunk_id'])
"
```
Expect `embedding dim: 384` (MiniLM-L6-v2's output size) and `chunk_count`
matching the total chunks across all 5 schemes.

## Troubleshooting

**First run is slow / downloading files.**
Normal — the model downloads once and is cached locally
(`~/.cache/huggingface`) for all future runs.

**Running on a machine with no internet after the first download.**
Fine — sentence-transformers uses the local Hugging Face cache once the
model has been downloaded once.

**Out of memory / very slow on a low-spec machine.**
MiniLM-L6-v2 is already the lightweight option per the PRD; if needed,
reduce `batch_size` in `embed_texts()` calls (default 32) in
`src/ingestion/embedder.py`.

## Next phase
Once `data/embeddings/chunk_embeddings.json` looks correct, you're ready for
**Phase 4 — Vector Store** (`src/retrieval/vector_store.py`), per
`docs/architecture.md`.

---

# Phase 4: Vector Store

Loads the cached embeddings from Phase 3 and persists them into a local,
on-disk ChromaDB collection at `data/vector_db/chroma`. Uses `upsert()`
keyed on `chunk_id`, so re-running this after a re-ingestion overwrites
existing records instead of duplicating them.

## 1. Install dependencies (adds chromadb)
```bash
pip install -r requirements.txt
```

## 2. Run the vector store loader (after Phase 3 has produced chunk_embeddings.json)
```bash
python -m src.retrieval.vector_store
```
You'll see a per-category breakdown in the logs, e.g.:
```
Large Cap: 29 chunks
Mid Cap: 31 chunks
Small Cap: 27 chunks
```

## 3. Verify the collection
```bash
python3 -c "
from src.retrieval.vector_store import get_collection
c = get_collection()
print('total records:', c.count())
print(c.peek(limit=2))
"
```

## 4. Try a semantic search (retriever.py)
```bash
python -m src.retrieval.retriever "What is the expense ratio of HDFC Small Cap Fund?"
```
Optional args: `top_k` and an exact `category` filter (`"Large Cap"`,
`"Flexi Cap"`, `"ELSS"`, `"Mid Cap"`, `"Small Cap"`):
```bash
python -m src.retrieval.retriever "lock-in period" 3 "ELSS"
```
You should see the top matching chunks ranked by similarity score, each
showing its scheme, fact type, source URL, and a text preview.

## Troubleshooting

**`FileNotFoundError: chunk_embeddings.json not found`**
Run Phase 3 (`python -m src.ingestion.embed_chunks`) first.

**Collection count doesn't match chunk count.**
Usually means two chunks in Phase 2 output share the same `chunk_id` (the
loader logs a warning with both numbers) — check `data/chunks/*_chunks.json`
for duplicate IDs.

**Want to rebuild the vector store from scratch.**
Delete the folder and re-run:
```bash
rm -rf data/vector_db
python -m src.retrieval.vector_store
```

## Note on this run's scope
Per your current status, `data/raw` and `data/chunks` only have 3 of the 5
schemes populated (Large/Mid/Small Cap — Flexi Cap and ELSS pending). The
vector store will simply contain whatever chunks exist at run time; re-run
Phase 1–3 for the remaining two schemes and re-run this phase (it's
idempotent) once they're ready.

## Next phase
Once the collection count looks right and `retriever.py` returns sensible
top matches for a few test questions, you're ready for **Phase 5 —
Retrieval Logic** (guardrails + prompt building + Mistral call), per
`docs/architecture.md`.
