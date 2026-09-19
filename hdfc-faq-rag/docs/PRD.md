# Product Requirements Document: HDFC Mutual Fund FAQ Assistant (RAG Prototype)

**Author:** Chintham Keerthisri
**Status:** Draft v1.0
**Date:** September 4, 2026

---

## 1. Overview

A retrieval-augmented generation (RAG) chatbot prototype that answers factual, sourced questions about five HDFC mutual fund schemes, using only their official Groww (Direct Growth) pages as the knowledge base. The assistant is strictly facts-only — it does not give investment advice, does not compute or compare returns, and cites its source in every answer.

## 2. Problem Statement

Retail investors researching mutual funds have to dig through scheme pages to find simple facts like expense ratio, lock-in period, minimum SIP, or exit load. A narrow, well-sourced FAQ assistant can answer these quickly while avoiding the risks of hallucinated numbers or implied investment advice.

## 3. Goals

- Build a working RAG prototype that answers factual queries about 5 specific HDFC schemes.
- Ground every answer in the official Groww Direct Growth page for that scheme, with a visible citation link.
- Refuse opinion/portfolio questions gracefully, redirecting to educational content.
- Demonstrate a clean, minimal ingestion → retrieval → generation pipeline others can inspect and extend.

## 4. Non-Goals (Out of Scope)

- No coverage of any scheme, AMC, or source beyond the 5 listed URLs.
- No performance computation, return comparison, or ranking of funds.
- No portfolio, suitability, or "buy/sell/hold" recommendations.
- No PII collection or storage of any kind.
- No mobile app; this is a desktop-first Streamlit prototype.
- No authentication, multi-user accounts, or persistence of chat history beyond the session.

## 5. Users

- **Primary:** Retail mutual fund investors researching HDFC's Large Cap, Flexi Cap, ELSS, Mid Cap, and Small Cap funds.
- **Secondary:** NextLeap fellowship reviewers assessing the prototype.

## 6. Scope: Data Sources

Exactly 5 URLs, all Groww Direct Growth pages, treated as the sole source of truth:

| Category | Scheme | URL |
|---|---|---|
| Large Cap | HDFC Large Cap Fund | https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth |
| Flexi Cap | HDFC Flexi Cap Fund | https://groww.in/mutual-funds/hdfc-flexi-cap-fund-direct-growth |
| ELSS | HDFC ELSS Tax Saver Fund | https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-growth |
| Mid Cap | HDFC Mid Cap Opportunities Fund | https://groww.in/mutual-funds/hdfc-mid-cap-opportunities-fund-direct-growth |
| Small Cap | HDFC Small Cap Fund | https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth |

No third-party blogs, no app back-end screenshots, no sources beyond these 5 pages.

## 7. Functional Requirements

### 7.1 FAQ Assistant Behavior

- **Answers factual queries only**, e.g.:
  - "Expense ratio of [scheme]?"
  - "ELSS lock-in period?"
  - "Minimum SIP amount?"
  - "Exit load?"
  - "Riskometer / benchmark?"
  - "How to download capital-gains statement?"
- **Citation required:** Every answer includes exactly one clear citation link back to the source Groww page used.
- **Refusal behavior:** Opinionated or portfolio questions (e.g., "Should I buy this fund?", "Which is best for me?") are politely refused with a facts-only message and a link to relevant investor-education content (not a fund page).
- **Answer length:** ≤3 sentences per answer.
- **Freshness disclosure:** Every answer appends "Last updated from sources: [date]" reflecting when the source pages were last ingested.
- **No performance claims:** If asked about returns/performance, the assistant declines to compute or compare and instead links to the official factsheet.

### 7.2 UI Requirements

- Minimal single-page Streamlit app.
- Welcome line explaining the assistant's purpose.
- 3 example questions shown as clickable prompts.
- Visible note: **"Facts-only. No investment advice."**
- Visual style: colors matching the Groww brand palette (deep navy/green primary, white background, Groww's signature green accent).
- Single chat input box, response area with citation link rendered distinctly (e.g., as a footer or badge under each answer).

### 7.3 Data Ingestion Pipeline

1. **Document upload/fetch:** Pull page content from the 5 specified Groww URLs only.
2. **Chunking:** Chunk each page's content using a strategy suited to the structured fact-sheet-style layout of the source pages (e.g., section-aware chunking so fields like expense ratio, exit load, lock-in, riskometer stay intact within a chunk, with scheme name/URL as metadata on every chunk).
3. **Embedding:** Generate embeddings using `sentence-transformers/all-MiniLM-L6-v2` (Hugging Face, free, lightweight, runs locally/CPU-friendly).
4. **Vector storage:** Store embeddings and chunk metadata (source URL, scheme name, category) in ChromaDB.

### 7.4 Data Retrieval & Generation Pipeline

1. **User question** submitted via UI.
2. **Query embedding:** Encode the question using the same MiniLM model used for ingestion.
3. **Retrieval:** Similarity search in ChromaDB to find the top relevant chunk(s), scoped to the matched scheme where identifiable.
4. **Prompt construction:** Build an LLM prompt containing the retrieved chunk(s), the source URL(s), and instructions enforcing: facts-only tone, ≤3 sentence limit, mandatory single citation, refusal rules for opinion/performance questions, and the "Last updated from sources" tag.
5. **Answer generation:** Call the Mistral API with the constructed prompt to generate the final answer.
6. **Response rendering:** Display the answer plus its single citation link in the Streamlit UI.

## 8. Constraints & Guardrails

- **Public sources only:** No app back-end screenshots; no third-party blogs as sources — only the 5 official Groww URLs.
- **No PII:** The system must not accept or store PAN, Aadhaar, account numbers, OTPs, emails, or phone numbers. Any user input resembling PII should be rejected/redacted before processing, and nothing is persisted beyond the active session.
- **No performance claims:** No return computation or comparison; performance questions are redirected to the official factsheet link.
- **Clarity & transparency:** All answers ≤3 sentences, each with exactly one citation and a "Last updated from sources: [date]" tag.
- **Scope lock:** Any question outside the 5 schemes/sources is declined as out of scope.

## 9. Example Interactions

**Q: "What is the expense ratio of HDFC Small Cap Fund?"**
A: States the expense ratio as found in the source chunk, ≤3 sentences, with the Groww Small Cap Fund link and last-updated tag.

**Q: "What's the lock-in period for HDFC ELSS Tax Saver Fund?"**
A: States the lock-in period (statutory 3 years for ELSS, confirmed from source), citing the ELSS scheme page.

**Q: "Should I invest in HDFC Mid Cap Opportunities Fund right now?"**
A: Polite refusal — "This assistant only provides factual scheme information and can't offer investment advice." Links to an investor-education resource (e.g., SEBI/AMFI investor education page), not a fund page.

## 10. Success Metrics (Prototype Stage)

- Correctly answers ≥90% of factual test questions across all 5 schemes with accurate citations.
- 100% of opinion/portfolio-style test questions are refused appropriately.
- 0 instances of PII being stored or echoed back.
- 0 instances of performance/return claims being generated.
- All answers conform to the ≤3-sentence and citation-tag format.

## 11. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Source pages change layout, breaking chunking | Re-run ingestion periodically; validate chunk extraction against known fields |
| LLM hallucinates facts not in retrieved chunks | Strict prompt instructions to answer only from retrieved context; refuse if chunk doesn't contain the answer |
| User submits PII | Input-side detection/rejection before the query reaches the LLM |
| Ambiguous scheme in query (e.g., user says "HDFC fund" without specifying) | Assistant asks for clarification or lists the 5 covered schemes |
| Question about performance/returns | Hard-coded refusal path bypassing retrieval, links to official factsheet |

## 12. Tech Stack Summary

| Layer | Choice |
|---|---|
| Chunking & orchestration | Python |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 (Hugging Face) |
| Vector store | ChromaDB |
| LLM | Mistral API |
| UI | Streamlit, styled with Groww brand colors |

## 13. Open Questions

- Exact re-ingestion cadence for the "Last updated from sources" timestamp (manual trigger vs. scheduled refresh).
- Whether category-level queries (e.g., "compare lock-in across all 5 schemes") are treated as factual (allowed) or comparative (needs a defined boundary, since it's not a performance claim but is a multi-scheme lookup).
- Exact wording/link for the educational redirect on refusals (e.g., SEBI or AMFI investor education page).
