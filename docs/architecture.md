# Architecture: HDFC Mutual Fund FAQ Assistant (RAG Prototype)

**Author:** Chintham Keerthisri (Snr Architect view)
**Status:** Draft v1.0
**Scope:** Strictly limited to the PRD — 5 HDFC Direct Growth scheme pages on Groww, MiniLM embeddings, ChromaDB, Mistral LLM, Streamlit UI. No feature, source, or component beyond the PRD is included.

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         STREAMLIT UI                         │
│   Welcome line · 3 example Qs · "Facts-only" note · Chat box │
└───────────────────────────────┬───────────────────────────────┘
                                 │ user question
                                 ▼
                    ┌────────────────────────┐
                    │   Guardrail Layer       │
                    │  (PII check, refusal    │
                    │   rules, scope check)   │
                    └────────────┬────────────┘
                                 │ clean query
                                 ▼
                    ┌────────────────────────┐
                    │   Query Embedding       │
                    │  (MiniLM-L6-v2)         │
                    └────────────┬────────────┘
                                 │ vector
                                 ▼
                    ┌────────────────────────┐
                    │   ChromaDB Retrieval    │
                    │  (top-k chunks + meta)  │
                    └────────────┬────────────┘
                                 │ retrieved chunks
                                 ▼
                    ┌────────────────────────┐
                    │  Prompt Builder         │
                    │  (context + rules)      │
                    └────────────┬────────────┘
                                 │ prompt
                                 ▼
                    ┌────────────────────────┐
                    │   Mistral API (LLM)     │
                    └────────────┬────────────┘
                                 │ answer + citation
                                 ▼
                          Streamlit UI (render)

   ── offline, one-time / periodic ──
   5 Groww URLs → Loader → Chunker → Embedder (MiniLM) → ChromaDB
```

Two pipelines: an **offline ingestion pipeline** (runs once, re-run on refresh) and an **online query pipeline** (runs per user question). Both are built and validated phase by phase below.

---

## 2. Phase 1 — Data Loading

**Goal:** Pull raw page content from exactly the 5 approved URLs, nothing else.

- **Input:** Hardcoded list of 5 URLs (Large Cap, Flexi Cap, ELSS, Mid Cap, Small Cap — all `-direct-growth` Groww pages).
- **Component:** `loader.py` — fetches each page's HTML and extracts the visible fact fields (expense ratio, exit load, lock-in, minimum SIP, riskometer, benchmark, fund details, etc.).
- **Output:** One raw document per scheme, each tagged with `{scheme_name, category, source_url, fetched_at}` metadata.
- **Guardrail:** Loader is hardcoded to only the 5 URLs — no crawling, no following links, no other domains.
- **Exit criteria:** 5 raw documents saved locally (e.g., as JSON/HTML snapshots), one per scheme, each with metadata populated.

## 3. Phase 2 — Chunking

**Goal:** Split each scheme's document into small, fact-coherent chunks.

- **Approach:** Section-aware chunking — each chunk maps to one logical fact group (e.g., "expense ratio + exit load", "lock-in + minimum SIP", "riskometer + benchmark", "how to download capital-gains statement") rather than fixed-size token windows, so a single fact is never split across chunks.
- **Metadata carried per chunk:** `scheme_name`, `category`, `source_url`, `fetched_at`.
- **Output:** A list of chunks per scheme (small in number, since each source page is short and structured).
- **Exit criteria:** Every fact type named in the PRD (expense ratio, lock-in, min SIP, exit load, riskometer/benchmark, capital-gains statement how-to) is present in exactly one identifiable chunk per relevant scheme.

## 4. Phase 3 — Embedding

**Goal:** Convert chunks (and later, queries) into vectors using one consistent model.

- **Model:** `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face) — same model used for both ingestion-time chunk embedding and query-time embedding.
- **Component:** `embedder.py` — thin wrapper so ingestion and retrieval never diverge in embedding logic.
- **Output:** One vector per chunk, paired with its metadata.
- **Exit criteria:** All chunks from Phase 2 have embeddings generated with no errors; embedding function is reusable as-is for query time.

## 5. Phase 4 — Vector Store

**Goal:** Persist chunk vectors + metadata for retrieval.

- **Store:** ChromaDB (local persistent collection).
- **Schema per record:** `id`, `embedding`, `chunk_text`, `scheme_name`, `category`, `source_url`, `fetched_at`.
- **Component:** `vector_store.py` — handles collection creation, upsert on re-ingestion (so re-running Phase 1–3 doesn't duplicate records), and simple similarity query interface.
- **Exit criteria:** Collection contains exactly the chunks from the 5 schemes (no orphaned or duplicate records); a basic `count()` check matches expected chunk totals.

## 6. Phase 5 — Retrieval Logic

**Goal:** Given a user question, return the right chunk(s) and enforce the PRD's behavior rules before generation.

- **Steps:**
  1. **Guardrail check** (pre-retrieval): reject/redact PII patterns; detect opinion/portfolio-style questions (e.g., "should I", "which is better") and route straight to the refusal path, skipping retrieval; detect performance/return questions and route to the factsheet-link refusal path, skipping generation.
  2. **Scheme disambiguation:** if the query names a scheme/category, filter retrieval to that scheme's chunks; if ambiguous, either ask for clarification or search across all 5 and surface only if one scheme's chunk clearly dominates.
  3. **Similarity search:** embed the query (Phase 3 model) and fetch top-k chunks from ChromaDB (Phase 4).
  4. **Prompt construction:** inject retrieved chunk text + source URL + system rules (≤3 sentences, one citation, "Last updated from sources" tag, no fabrication beyond retrieved context) into the Mistral prompt.
  5. **Generation call:** send to Mistral API, return answer + citation to the UI.
- **Component:** `retriever.py` + `prompt_builder.py`.
- **Exit criteria:** For each of the PRD's example question types (expense ratio, lock-in, min SIP, exit load, riskometer/benchmark, capital-gains download), the pipeline returns a chunk from the correct scheme and produces a properly formatted answer.

## 7. Phase 6 — Retrieval Testing

**Goal:** Validate accuracy, refusal behavior, and guardrails end-to-end before calling the prototype done.

- **Test set (aligned to PRD):**
  - Factual questions × 5 schemes (expense ratio, lock-in, min SIP, exit load, riskometer/benchmark, capital-gains statement) — verify correct scheme, correct chunk, citation present, ≤3 sentences, timestamp present.
  - Opinion/portfolio questions ("Should I buy X?", "Which is best for me?") — verify polite refusal + educational link, no fund page linked as the "citation."
  - Performance/return questions ("What were the 5-year returns?") — verify refusal + link to official factsheet, no computed numbers.
  - Out-of-scope questions (other AMCs, other schemes, general market questions) — verify decline as out of scope.
  - PII inputs (sample PAN/phone/email patterns) — verify rejection/redaction, nothing persisted.
- **Method:** Simple scripted test harness (`test_retrieval.py`) running the fixed question set against the live pipeline, logging pass/fail against the exit criteria in Section 6 and the PRD's Section 10 success metrics.
- **Exit criteria:** ≥90% pass rate on factual questions with correct citations; 100% pass rate on refusal and PII-rejection cases, matching PRD success metrics.

---

## 8. Component Summary

| Component | Responsibility | Phase |
|---|---|---|
| `loader.py` | Fetch the 5 fixed URLs | 1 |
| `chunker.py` | Section-aware chunking | 2 |
| `embedder.py` | MiniLM embedding (shared by ingestion + query) | 3 |
| `vector_store.py` | ChromaDB read/write | 4 |
| `retriever.py` | Guardrails + scheme filter + similarity search | 5 |
| `prompt_builder.py` | Build the constrained Mistral prompt | 5 |
| `llm_client.py` | Call Mistral API | 5 |
| `test_retrieval.py` | Scripted test harness | 6 |
| `app.py` | Streamlit UI | — |

## 9. Constraints Carried From PRD (Non-Negotiable)

- Only the 5 named Groww URLs — no other sources, no crawling.
- No PII stored or echoed.
- No performance computation or comparison — factsheet link only.
- Every answer: ≤3 sentences, exactly one citation, "Last updated from sources" tag.
- Opinion/portfolio questions always refused with an educational (non-fund) link.
