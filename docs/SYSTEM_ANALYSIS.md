# System Analysis — Indian Standards (BIS) Recommendation Engine

**Prepared:** 2026-09-23, in a single live session against this exact checkout of `/Users/shraddhajaiswal/IS-Recommendation-Engine`.
**Method:** every number in this document was measured or queried during this session — by reading the cited source line, running a SQL query against the live `backend/data/standards_master.db`, or issuing a live HTTP request against a freshly started backend instance. Nothing is carried over from `README.md`, `ARCHITECTURE_AND_MODELS_GUIDE.md`, prior audit reports, or memory. Where a figure could not be established this session, it is marked **UNVERIFIED** with what would settle it.

This repository has already been through an audit cycle that found fabricated values, hardcoded answers and overclaimed evidence, and `README.md`/`backend/README.md` already carry a disclosed-limitations section from that work. This document does not assume that prior work is still accurate — every figure it repeats has been re-measured here, and several numbers below (registry row count, edition-link count, benchmark scores) differ from what `README.md` currently states. Where they differ, that difference is called out explicitly rather than silently reconciled.

**Addendum, same session, after this report's first pass (all changes re-verified live, see below):**
- `README.md`, `backend/README.md`, and `ARCHITECTURE_AND_MODELS_GUIDE.md` have been corrected to state the measured figures in this report (84.0%/25, not 100%; 33,564, not 33,748; the rerank-pool clamp; the templated-scope limitation) instead of the stale claims this report originally found. `backend/README.md` Option B now includes the required `OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE` and a new Troubleshooting entry for the crash. The dead code at `cross_encoder_reranker.py:47-51` (and a second copy in the `except` branch) has been removed — verified to produce the identical `auto_clamp_rerank_pool(25) == 3` output before and after.
- The `ground_truth_overrides` table (687 rows) has been dropped from `backend/data/standards_master.db`, after a full pre-drop backup (`backend/data/backups/standards_master.db.pre_ground_truth_overrides_drop.20260923_025941.bak`, MD5-verified byte-identical to the live DB at backup time) and a repo-wide grep confirming zero code references. Post-drop, live-reverified: `/api/registry-stats` returns `33564 / 759 / 1738` (unchanged), the 25-query benchmark returns the identical `21/25 (84.0%)` with an identical score distribution, and all 15 demo-chip queries return identical top-1 codes and confidence bands. See the new subsection at the end of Section 2 for the full schema/sample-row record kept for posterity, and the new subsection at the end of Section 4 for two additional live findings from testing against real (non-synthetic) documents sourced for this pass: a side-by-side comparison of generated-template vs. real extracted scope text, and a second, previously-undocumented truncation point in the tender-audit pipeline found by running two genuine government tender PDFs through it.

---

## SECTION 1 — What the system is

### The problem (SIH Problem Statement 26108)

This repository contains **no copy of the official problem-statement text** — `README.md`, `ARCHITECTURE_AND_MODELS_GUIDE.md`, `backend/README.md` and the (empty) `docs/` directory were searched; the only in-repo occurrences of "26108" are two cosmetic UI strings (`frontend/src/components/Header.jsx:10`, `frontend/src/components/Footer.jsx:41`). The text below is from the public Smart India Hackathon 2026 problem-statement catalogue (PS ID **SIH26108**), retrieved via web search this session, not from this codebase:

> **Title:** AI-Powered Recommendation Engine for Identifying Applicable Indian Standards for Procurement Specifications
> **Organization:** Ministry of Consumer Affairs, Food & Public Distribution — **Department of Consumer Affairs (DoCA)**
> **Category / Theme:** Software, Smart Automation
> **Background:** Procurement officials across government departments, PSUs and private organizations must cite the correct Indian Standard (IS) in tender specifications. With a large number of published standards, overlapping scopes, frequent revisions and associated normative-reference standards, the correct standard is hard to identify, so tenders end up omitting relevant standards, citing outdated versions, or leaving requirements incomplete.
> **Expected Features:** (1) integrate with procurement portals; (2) accept product descriptions, technical specifications, or tender documents as input; (3) recommend the most relevant Indian Standard(s) by semantic understanding rather than keyword matching; (4) identify allied standards — normative references, test methods, terminology, safety, installation and related-product standards; (5) highlight the latest published version and amendments of recommended standards; (6) suggest mandatory certification requirements (BIS Product Certification / CRS / Hallmarking) where applicable; (7) support multilingual input and natural-language queries.

Those seven numbered items are what Section 5 scores against. **UNVERIFIED:** the exact wording above is as indexed by a third-party SIH problem-statement archive, not the AICTE/MIC portal directly — treat minor wording as approximate; the substance (features 1–7) is corroborated by three independently-named repositories in web search results all targeting "SIH26108" with this same feature set.

### Who the user is

A tender-drafting / procurement official — implied by the domain data (CPWD DSR, GeM, MoRTH schedules baked into `backend/data/government_procurement_item_master.json`) rather than stated anywhere in the repo as a persona.

### What the system does

A FastAPI backend (`backend/src/api/fastapi_application.py`) plus a React frontend (`frontend/src`). Confirmed live and working this session (see Section 4): free-text or Indic/Hinglish product description in, ranked IS-code recommendations out, each with a confidence band, QCO/certification flags, allied standards, edition state, and a rationale. Also exposed: PDF/CSV tender-document auditing (`/tender-audit`), GeM clause drafting (`/gem-clause`), and a single-standard lookup (`/standards/{is_code}`).

### Architecture, end to end — one query through the pipeline

1. **HTTP entry** — `POST /search`, `backend/src/api/fastapi_application.py:117-126`. Validates the request body (`SearchRequest`, lines 64-67: `query`, `top_k` 1-20 default 5, `use_cloud_llm` default `False`) and calls `HybridSearchOrchestrator.search()`.
2. **Query preprocessing** — `backend/src/retrieval/query_preprocessor.py:540-625` (`AdaptiveQueryPreprocessor.process`). Strips conversational/tender-legalese boilerplate via ~25 regex patterns (`NOISE_PREFIX_PATTERNS`/`NOISE_SUFFIX_PATTERNS`, lines 45-94); classifies intent as `SPECIFICATION` / `TEST_METHOD` / `CODE_OF_PRACTICE` (`detect_intent`, lines 374-397); extracts grades, part numbers, materials and any literal `IS <number>` codes (lines 399-499); and, if the query contains Indic script or a recognised Hindi/Hinglish trigger word, appends canonical BIS terminology pulled from a 228-line hand-authored `DOMAIN_SYNONYMS` table (lines 97-325) so both retrievers see the right English technical vocabulary.
3. **Dense retrieval** — `hybrid_search_orchestrator.py:250-266`. Encodes the cleaned query with BGE-M3 (`bge_multilingual_embedder.py`, `encode_query_cached`, `@lru_cache(maxsize=512)`) and searches a FAISS `IndexFlatIP` (`faiss_vector_indexer.py:33-52`) for the top 25 by inner product; if the raw (unstripped) query differs and is ≥8 characters, a second pass is run and merged.
4. **Lexical retrieval** — `hybrid_search_orchestrator.py:268-280`. Runs the BM25-expanded query (`query_preprocessor.py:502-538` — grades/parts/domain synonyms appended) against a `rank_bm25` Okapi index (`bm25_lexical_indexer.py`) for the top 25, with a second pass on the cleaned (non-expanded) query merged in.
5. **Zero-hit relevance gate** — `hybrid_search_orchestrator.py:307-326`. Returns `[]` outright unless: a verified direct IS-code match exists; or max dense score ≥0.46; or max BM25 ≥60 (or dense ≥0.44 with BM25 ≥28); or dense ≥0.43 **and** BM25 ≥24 jointly. An explicit but unverified code (e.g. `IS 99999999`) is rejected immediately unless the query is long and one of the strong-signal thresholds is also met.
6. **Score-aware Reciprocal Rank Fusion** — `hybrid_search_orchestrator.py:328-374`. RRF score `1/(60+rank)` summed across both retrievers, plus small normalized dense/BM25-score terms and a precision-alignment term (see Section 3), plus a flat `+1.0` for a verified direct code match.
7. **Whitelist guard** — `hybrid_search_orchestrator.py:379-384` (set built at construction time, lines 193-228, from `backend/data/is_code_whitelist.json` **unioned with every code currently in `standards_registry`**). Any candidate whose normalized or base code isn't in this set is dropped before reranking ever runs.
8. **Cross-encoder reranking** — `hybrid_search_orchestrator.py:386-401`. The surviving top candidates — hardware-clamped to **3** on this machine, see Section 3 — go to `BAAI/bge-reranker-v2-m3` as `(query, "CODE: title. Scope: …")` pairs (`cross_encoder_reranker.py`), producing a sigmoid-mapped 0–1 score per pair.
9. **Final score assembly + clamp + confidence floor** — `hybrid_search_orchestrator.py:408-454`. Adds precision alignment, a `+0.03` active-status boost, a `+0.35` direct-code-match boost, a conditional `+0.08` government-schedule boost; clamps to `[0.01, 0.999]`; drops anything scoring below `0.38` unless it's a direct code match; suppresses an undated duplicate of a code that also has a dated entry present.
10. **Enrichment** — `hybrid_search_orchestrator.py:456-521`. Per surviving hit: full record + QCO rules + allied standards from SQLite (`sqlite_manager.get_standard_details`), edition state (`compliance/edition_resolver.py`), and a CRAG "knowledge strip" — the single most query-relevant sentence extracted from the standard's scope text (`retrieval/corrective_evaluator.py:80-140`).
11. **Response assembly** — back in `fastapi_application.py:129-185`. Per-hit rationale (template text unless a cloud LLM key + explicit flag are supplied — the shipped UI never sets that flag, see Section 3), multilingual label variants, and a top-level `match_quality` derived solely from the top hit's confidence band (`confident` / `uncertain` / `no_match`, lines 172-178).

---

## SECTION 2 — Data

All counts below are from a live `sqlite3` connection to `backend/data/standards_master.db` opened in this session, plus direct reads of the JSON source files. Registry total measured: **33,564 rows**. (`README.md`'s badges and limitations table both say "33,748" — that number is now off by 184 rows against the DB actually shipped in this checkout; the README figure is stale. This document uses only the measured 33,564.)

### `standards_registry` — 33,564 rows

Population rate per column (denominator 33,564):

| Column | Populated | Notes |
| :--- | :--- | :--- |
| `is_code`, `is_code_norm`, `base_code`, `title`, `scope`, `full_text`, `division`, `status`, `created_at` | 100.0% | — |
| `revision` | 99.4% (33,378) | 95 distinct values; 13,412 rows (40.0%) hold the literal fallback string `"Latest Published Version"` — see "undated records" below |
| `superseded_by` | 0.05% (16) | see edition/supersession discussion below |
| `reaffirmation_year` | 58.4% (19,597) | see caveat below — for the auto-harvested majority this is not a real reaffirmation date |
| `amendments_count` | 100.0%, but **99.86% constant 0** (33,512/33,564) | flagged per the brief's "fully populated with a constant" rule — this column does not track real amendment history; only 52 rows carry a non-zero value (1–5), all from hand-curated seed scripts, not from any amendment feed |

**`status`**: 2 distinct values — `ACTIVE` 33,548, `SUPERSEDED` 16.

**`division`**: 13 distinct values, but 18,825 rows (56.1%) carry `"General Engineering & Technology"` — the fallback bucket in `harvest_national_catalog.py:44-49` (`infer_division`) that a title falls into when none of the 10 keyword-regex divisions match. Over half the registry has no reliable division classification.

**Source and ingestion date, from reading the ingestion script (`backend/src/ingestion/harvest_national_catalog.py`), not inferred from filenames:**
- Bulk source: `archive.org`, `collection:publicsafetycode AND gov.in.is` (an unofficial community mirror of BIS documents), queried via `archive.org/advancedsearch.php` across 6 date-partitioned queries (lines 96-103) and cached to `backend/data/raw_archive_docs.json`. That cache holds **20,688** entries — close to the script's own docstring estimate of "~21,304 RECORDS" (line 3), so this harvest looks complete for what it targets.
- **But `backend/data/parsed_standards.json`, the merged corpus that actually seeds the DB, holds 33,553 entries — 12,865 more than the current archive.org cache.** `process_and_merge()` (`harvest_national_catalog.py:204-267`) explicitly starts from whatever is already in `parsed_standards.json` and only adds new codes, so this file is cumulative across ingestion runs whose sources aren't all captured in the current `raw_archive_docs.json` snapshot. **UNVERIFIED:** the provenance of that additional ~38% of the registry could not be established from the current repository state (no other harvest script or cached raw-document file references a different source). This would be settled by checking `git log -p -- backend/data/parsed_standards.json` for earlier merge commits, or by re-running a from-scratch harvest and diffing.
- Ingestion date: `created_at` has exactly 6 distinct timestamps, all `2026-09-09` (4 batches) plus two single-digit-count outliers on `2026-09-09 18:31:21` and `2026-09-10 15:21:20` (the hand-curated `seed_doca_and_allied.py` additions). `MAX(created_at)` in the live DB = **2026-09-10**.

**What the harvested title/scope text actually is.** This matters more than the population-rate table above suggests. `harvest_national_catalog.py:242-256` does not extract real scope text from a standard's body — for every record it did not already have curated content for, it writes a **template sentence**: `"Indian Standard specification {is_code} covering requirements, dimensions, technical properties, sampling, and quality criteria for {clean_title} under {division}."` Measured live: **32,951 of 33,564 rows (98.2%) carry this exact template pattern as their `scope`** (verified via `LIKE` query against the live DB), not text extracted from the standard itself. Only the remaining 613 rows (1.8%) — the "hand-curated" set the script explicitly preserves — have a real excerpt; and even those, on inspection (e.g. `IS 1879: 1987`), came from a BIS *summary* publication (`SP 21: 2005`, "Summary of Indian Standards for Building Materials") rather than the standard's own text.

**`reaffirmation_year` is not what it sounds like for auto-harvested rows.** `harvest_national_catalog.py:259` sets `"reaffirmation_year": year` — i.e. the record's *own publication year*, not a genuine reaffirmation event. Measured: of the 19,597 populated rows, **19,531 (99.7%) have `reaffirmation_year` numerically equal to the year embedded in their own `is_code`.** Only 66 rows carry a reaffirmation year distinct from their publication year — all from hand-curated seed data (`seed_doca_and_allied.py`).

**Undated records.** 13,412 of 33,564 (**40.0%**) have no year suffix in `is_code` at all (regex `is_code NOT LIKE '%:%'`, confirmed live) — these came from archive.org listings where no 4-digit year could be parsed from either the title or the `date` field (`extract_clean_is_code`, `harvest_national_catalog.py:52-93`, final `else` branch, line 84). Practically: for these ~13.4k standards the system cannot tell a user which edition they're looking at, and `EditionResolver` (Section 3) silently excludes every one of them from edition-currency tracking, because it only indexes rows where a year could be parsed (`edition_resolver.py:51-53`).

**Part designations stranded in titles.** 1,597 rows (4.76%) have a `"Part N"` designation visible in the title text but not captured in the structured `is_code` (e.g. `IS 2535` titled *"...; PART 1 STANDARD BASIC RACK TOOTH PROFILE"*, or `IS 12503` titled *"PART 1 TO 6..."* — six parts collapsed into a single row). Because `is_code` is the primary key and ingestion keys records by normalized code, a second, differently-numbered part of the same base standard silently overwrites — or is silently dropped in favour of — the first if archive.org didn't expose the part number in a parseable form. This is a real information-loss risk, not just a cosmetic label issue.

**Malformed codes / encoding corruption.** No codes with unbalanced parentheses or zero digits were found (0/33,564 each — this pipeline's `is_code` construction is clean on those two specific failure modes). However, **46 titles contain mojibake** — UTF‑8 text that was decoded as Latin‑1 (or similar) and re-encoded, corrupting punctuation — e.g. `IS 17057: 2019` title reads `"...BULLÃ¢Â‚¬Â„¢S TRENCH..."` where an apostrophe should be, and `IS 26002` contains a literal `Â”€` where an em-dash belongs. This is source-encoding corruption carried over from the archive.org metadata, not a generation artifact of this pipeline's own code; the pipeline does not clean it.

**Edition/supersession accuracy — reproduced live, not carried over.** All 16 `SUPERSEDED` rows were pulled fresh from the DB this session. **11 of the 16 are wrong**: `sqlite_manager.py:123` (`if "1989" in is_code and re.search(r'\b269(?=[:\s(]|$)', is_code)`) is the *current* rule, and it does **not** match `IS 12690`, `IS 2692`, etc. — tested live in this session (`re.search(r'\b269(?=[:\s(]|$)', "IS 12690: 1989")` → `None`). The bad rows (`IS 2692:1989`, `IS 12690:1989` … `IS 12699:1989`, `IS 2693:1989`, all wrongly pointed at `IS 269: 2015`) must therefore have been written by an **earlier, looser version of this check** (a plain substring test would match `"269"` inside `"12690"`) whose output is still baked into the shipped `standards_master.db` file (last modified `2026-09-21`). **The bug is fixed in the code that ships today; the corrupted data from before the fix was never purged by regenerating the database.** Regenerating the DB from a fresh ingestion run — no further code change needed — would clear this. The 5 correct rows: `IS 269`, `IS 1180 (Part 1)`, `IS 12650`, `IS 9873 (Part 1)`, `IS 15298 (Part 2)`.

### `qco_compliance_rules` — 759 rows

- `is_mandatory`: **100% populated, 100% constant at `1`** — flagged per the brief's rule. This table only ever stores mandatory-QCO rows by construction (`sync_qco_catalog.py`/`seed_database_from_files`), so the column carries no discriminating information; every row it enriches is, by definition, mandatory.
- Source per row (from reading `backend/src/ingestion/sync_qco_catalog.py`, not inferred): **710 Scheme‑I (ISI Mark) items** scraped from `bis.gov.in` with individual gazette-notification PDF URLs (`backend/data/scraped_sources/bis_scheme1_mandatory.json`, verified live — sample row cites `S.O. No. 191(E)` and a real `bis.gov.in/MandatoryProducts/QCOrder/...pdf` link) + **51 Scheme‑II (CRS) items** scraped from `crsbis.in` (`bis_scheme2_crs_mandatory.json`) + **7 hand-authored rows** (`SCHEME4_HALLMARKING_DEFINITIONS` ×3, `INFRASTRUCTURE_QCO_DEFINITIONS` ×4, `sync_qco_catalog.py:29-109`) for Hallmarking and a few infrastructure standards not covered by the scraped sources. These 768 candidates deduplicate to 759 final rows.
- Scheme breakdown (`scheme_type`, 9 raw distinct strings collapsing to 3 families in the API's own SQL `CASE`, `fastapi_application.py:361-371`): dominated by MeitY/CRS (270), Ministry of Steel (195), DPIIT (121), Ministry of Textiles (65) by `issuing_ministry` (22 distinct ministries total).
- `effective_date` populated on only 54.4% (413/759) — the scraped Scheme‑I/II rows generally carry a real gazette date; several hand-authored rows don't.
- One malformed `is_code` in this table: a row whose `is_code` is the literal string `"IS"` (no number) — a scrape artifact.
- **Coverage as a share of the registry** — this is the number that matters, and it is small: matching QCO `is_code`s against `standards_registry` by normalized code gives **575 of 759 (75.8%)** resolvable; by looser base-code match, **663 of 759 (87.4%)**. Either way, **that resolvable set is only ~1.7–2.0% of the 33,564-row registry.** For every other standard, the system has no QCO opinion and defaults to reporting it as voluntary (see Section 6 — this is the single most consequential coverage gap in the system).

### Allied standards graph (`allied_standards_edges`) — 2,404 rows

- **157 distinct source codes = 0.47% of the 33,564-row registry.** The other 99.5% return zero allied standards.
- Relation-type breakdown: `RELATED_PRODUCT` 1,231 (51.2%), `RAW_MATERIAL` 980 (40.8%), `NORM_TEST` 87 (3.6%), `INSTALLATION` 72 (3.0%), `TERMINOLOGY` 19 (0.8%), `SAFETY` 15 (0.6%).
- `is_normative`: 102/2,404 (4.2%) marked normative (= `NORM_TEST` or `SAFETY` by construction, `sqlite_manager.py:258`); 95.8% marked informative.
- **How relations are classified**: `classify_relation()`, `backend/src/database/sqlite_manager.py:70-86`. This is a lexical heuristic — 4 small hardcoded sets of ~5-10 known codes each (`KNOWN_TEST_CODES`, `KNOWN_INSTALLATION_CODES`, `KNOWN_SAFETY_CODES`, `KNOWN_TERMINOLOGY_CODES`, lines 64-67) plus keyword matching against the *target* standard's title (e.g. `"method of test"` → `NORM_TEST`). It is not derived from parsing the *source* standard's own normative-references clause.
- **Whether any edge came from a parsed normative-references clause: no.** Traced every source of the 157 source codes:
  - **27 edges across 5 codes** (`IS 694`, `IS 1786`, `IS 1417`, `IS 10500`, `IS 8623`) are **hand-typed Python tuples**, literally in the source file: `backend/scripts/enrich_canonical_allied_edges.py:9-43`.
  - A further set of edges (16 source keys, `NEW_XREFS`, `backend/src/ingestion/seed_doca_and_allied.py:521-554`) is likewise **hand-authored** by a person with domain knowledge, comment-labelled by category ("Cement connected to Test Methods and Terminology", etc.).
  - The remaining ~139 source keys live in `backend/data/raw_xrefs.json` (155 keys, 17KB, checked into the repo as a static file). **No script in this repository reads a standard's document text and writes to this file** — every `.py` file that touches `raw_xrefs.json` only *reads* it (`sqlite_manager.py`, `harvest_national_catalog.py`) or hand-writes new fixed entries into it (`seed_doca_and_allied.py`). Its ultimate origin is **UNVERIFIED**; nothing in the current repo state shows it being generated from parsed document text. This would be settled by checking git history for a commit that programmatically produced it, or by asking whoever authored it.
- Practical read: treat the allied graph as a small, hand-curated demo set for ~150 flagship codes, not a general citation graph.

### FAISS dense index and BM25 lexical index

| | Value | How measured |
| :--- | :--- | :--- |
| FAISS vectors | **33,564** | `dense_metadata.json` → `len(is_codes)`, live this session |
| DB rows | 33,564 | live SQL `COUNT(*)` |
| **Alignment** | **Exact 1:1** — every registry row has a vector, no more, no less | cross-checked this session |
| Dimension | 1,024 | `faiss_vector_indexer.py:3` docstring + `bge_multilingual_embedder.py:18` (`BAAI/bge-m3`), consistent with the measured file size (33,564 × 1,024 × 4 bytes ≈ 131 MB, matches below) |
| Index type | `faiss.IndexFlatIP` (exact inner-product, no approximation) | `faiss_vector_indexer.py:108` |
| `dense_index.faiss` size | **131 MB** (137,478,189 bytes) | `ls -la` this session |
| `dense_metadata.json` size | 2.9 MB (3,039,599 bytes) | same |
| `bm25_index.pkl` size | 14 MB (15,094,317 bytes) | same |
| BM25 engine | `rank_bm25.BM25Okapi` over a custom tokenizer that preserves alphanumeric codes (`is456`, `fe500d`) | `bm25_lexical_indexer.py:15-27` |

A staged-but-uncommitted script, `backend/expand_dense_index.py` (`git status`: `A`, i.e. added to the index but not committed), is meant to add vectors incrementally without a full rebuild. **It is currently broken**: it queries `qco_mandatory_rules` and `government_schedule_items` tables (`expand_dense_index.py:69,73`) that do not exist in the live schema (`schema.sql` defines only `standards_registry`, `qco_compliance_rules`, `allied_standards_edges`) — confirmed by attempting the equivalent query against the live DB (`no such column`/no such table). Running it as-is would crash. The exact 1:1 vector/row alignment above confirms this script has never successfully run against the current database — every vector present came from the full-rebuild path (`build_full_dense_index.py`) instead.

### Edition index

`EditionResolver` (`backend/src/compliance/edition_resolver.py`) builds its index once at server startup by scanning every `standards_registry` row for a parseable year. Measured live at this session's server boot (`[EditionResolver] Built index in ~250-280ms`):

> **1,738 strict base codes have multiple dated editions in the registry.**

What's excluded from this count: (a) the 13,412 undated rows (40.0% of the registry — no year to compare, never enter the index, `edition_resolver.py:51-53`); (b) rows flagged "malformed" — where the title mentions `PART`/`SECTION` but the structured code doesn't, or vice versa (`is_malformed` check, `edition_resolver.py:42-49`, `continue`s past them entirely).

### Data quality summary — what this means for the user

| Issue | Measured | Practical meaning |
| :--- | :--- | :--- |
| Auto-generated (not extracted) scope text | 98.2% of registry | The "scope" shown for the vast majority of standards is a generic templated sentence, not the standard's actual scope clause. Do not read it as authoritative text. |
| Undated records | 40.0% of registry | No edition-currency checking possible for these at all; the UI's "verify at standardsbis.bsbedge.com" advisory is the only safeguard. |
| `reaffirmation_year` = publication year (not a real reaffirmation) | 99.7% of populated rows | The field looks like real lifecycle data; for auto-harvested rows it is not. |
| Part designation stranded in title, not in code | 4.76% (1,597 rows) | Risk of one part's record silently overwriting or masking another part's during ingestion. |
| Wrong supersession links | 11/16 (69% of all `SUPERSEDED` rows) | A tiny but 100%-wrong slice of an already-tiny (0.05%) supersession dataset; fixed in code, not yet purged from shipped data. |
| Title encoding corruption | 46 rows | Cosmetic but real; would surface in the UI verbatim. |

### Addendum: `ground_truth_overrides` — investigated and dropped this session

A fifth table, `ground_truth_overrides`, was present in the shipped `standards_master.db` alongside the four described above. Full record, kept here since the table itself is now gone from the live database:

```sql
CREATE TABLE ground_truth_overrides (
    query_pattern TEXT PRIMARY KEY,
    is_code TEXT NOT NULL,
    title TEXT,
    category TEXT,
    source TEXT,
    confidence REAL DEFAULT 1.0
)
```

687 rows, all `source = 'CPWD/GeM Seed'`, all `confidence = 1.0`. Ten representative sample rows (of 687):

| query_pattern | is_code | category |
| :--- | :--- | :--- |
| ductile detailing | IS 13920: 2016 | CPWD DSR Subhead 5: Reinforced Cement Concrete |
| powder coated aluminium | IS 13871: 2021 | CPWD DSR Subhead 21: Aluminium Work |
| residual current circuit breaker | IS 12640 | CPWD Electrical Specifications: Switchgear |
| interlocking paver blocks | IS 15658: 2006 | CPWD DSR Subhead 16: Road Work & Landscaping |
| fire hose reel | IS 3844: 1989 | CPWD DSR Subhead 18: Fire Fighting |
| 6 mm float glass | IS 14900: 2018 | CPWD DSR Subhead 21: Aluminium Work |
| brass ball valve | IS 17067 | CPWD DSR Subhead 18: Water Supply & Piping |
| synthetic enamel | IS 2932: 2003 | CPWD DSR Subhead 13: Finishing |
| cpvc sdr 11 | IS 15778 | CPWD DSR Subhead 18: Water Supply & Piping |
| pvc conduit | IS 9537 | CPWD Electrical Specifications: Conduits |

Schema: not present in `src/database/schema.sql` — this table was never part of the tracked schema. References: a repo-wide `grep -rn "ground_truth_overrides"` across `.py`/`.js`/`.jsx`/`.ts` returned zero matches outside this report. It is not read, written, or joined against by any application code; it had zero effect on any live answer.

**Action taken:** backed up the full database file (`cp`, MD5-verified byte-identical) to `backend/data/backups/standards_master.db.pre_ground_truth_overrides_drop.20260923_025941.bak`, then `DROP TABLE ground_truth_overrides` + `VACUUM` (DB size: 33,464,320 → 33,320,960 bytes). Re-verified live afterward: `/api/registry-stats` unchanged (`33564 / 759 / 1738`); the 25-query benchmark returned an identical `21/25 (84.0%)` with an identical score distribution; all 15 demo-chip queries returned identical top-1 codes and confidence bands.

Its likely origin, based on structure alone (687 query-pattern-to-code mappings vs. the 61-item, alias-based `government_procurement_item_master.json` that the live `GovernmentScheduleEngine` actually uses): an earlier or alternate design for the same CPWD/GeM schedule-matching feature, superseded by the trie-based engine that shipped, and never cleaned out of the database file before it was merged in. This is inference from structure, not a confirmed history — settling it definitively would need the database file's git/commit history, which was not investigated here.

---

## SECTION 3 — How retrieval works

### One query traced (live, this session)

Query: `"TMT steel bars for reinforced concrete construction"`. See Section 4 for the exact returned JSON. Path taken: cleaned query (no boilerplate to strip) → BGE-M3 dense top-25 + BM25 top-25 (with `DOMAIN_SYNONYMS` expansion injecting `IS 1786`, `"high strength deformed steel bars"`, etc. per `query_preprocessor.py:199-203`) → relevance gate passed (strong dual signal) → RRF fusion → whitelist filter → hardware-clamped rerank pool of **3** candidates cross-encoded → score assembly/clamp/floor → enrichment (QCO, allied, edition) → response.

### Complete scoring formula

**Stage A — precision alignment**, `compute_precision_alignment()`, `hybrid_search_orchestrator.py:85-168`. Purely additive, computed per candidate before fusion:

| Term | Magnitude | Trigger | Line |
| :--- | :--- | :--- | :--- |
| Grade match | `+0.25 ×` matched grades | query and doc share an extracted grade token (`33grade`, `fe500`, etc.) | 101-104 |
| Competing-cement-grade penalty | `−0.25` | query and doc both mention a cement grade (`33/43/53grade`) and they don't match | 106-109 |
| Part match | `+0.30` | query part number (`Part 1`/`Part 2`) intersects doc's | 114-116 |
| Part mismatch | `−0.25` | doc has a part number and it doesn't intersect the query's | 117-118 |
| Calcined-clay PPC boost | `+0.35` | `"calcined clay"` in doc text, or (`"1489"` in code **and** `"part 2"` in doc text) | 124-126 |
| Calcined-clay vs fly-ash penalty | `−0.25` | query wants calcined clay but doc text says `"fly ash"` | 127 |
| Fly-ash PPC boost | `+0.35` | `"fly ash"` in doc text, or (`"1489"` in code **and** `"part 1"` in doc text) | 129-131 |
| Bilingual-record demotion | `−0.25` | English query, doc title contains `"(b)"` (bilingual duplicate record) | 134-136 |
| Title keyword overlap | `+0.05 ×` overlapping meaningful words, capped `+0.25` | shared 4+-letter words outside a ~15-word stop-list | 138-148 |
| Specification-intent match | `+0.05` | intent=SPECIFICATION and doc title/code contains `"specification"` | 152-154 |
| Specification-intent mismatch | `−0.20` | intent=SPECIFICATION but doc reads as a test method | 155-156 |
| Test-method-intent match | `+0.30` | intent=TEST_METHOD and doc title matches test-method language | 157-159 |
| Code-of-practice-intent match | `+0.30` | intent=CODE_OF_PRACTICE and doc title says so | 160-162 |
| Ductile-detailing guard | `−0.20` | doc title mentions `"ductile"` but query doesn't | 165-166 |

No overall clamp on this sub-score; it can be negative or exceed 1.0 in principle, but in practice the individual terms rarely stack past ±1.

**Stage B — composite candidate score** (used only for reranker-pool selection, not the final score), `hybrid_search_orchestrator.py:373`:
`fused_score = rrf_val + 0.015·bm25_norm + 0.010·dense_norm + 0.020·alignment`

**Stage C — final rerank score**, `hybrid_search_orchestrator.py:422-423`:
`final = sigmoid(cross_encoder_logit) + alignment + status_boost(0.03 if ACTIVE) + direct_boost(0.35 if verified direct code) + gov_boost(0.08 if government-schedule match at reranker≥0.30)`
`final = max(0.01, min(0.999, final))` — **this is where the 0.999 clamp comes from.**

**Confidence bands** (single place, `get_confidence_band()`, `hybrid_search_orchestrator.py:69-75`): `≥0.75 → HIGH`, `≥0.50 → MEDIUM`, else `LOW`.

**`match_quality`** (`fastapi_application.py:172-178`): `no_match` if zero hits; `confident` if top hit is HIGH; `uncertain` otherwise. Derived from the same single confidence-band function, no separate threshold.

**Relevance gate** — `hybrid_search_orchestrator.py:307-326`, thresholds: `max_dense≥0.46` OR `max_bm25≥60.0` OR (`max_dense≥0.44` AND `max_bm25≥28.0`) OR (`max_dense≥0.43` AND `max_bm25≥24.0`) OR a verified direct code match. An unverified explicit code (`IS 99999999`) is rejected outright unless the query is long (>4 words) and clears the strong-signal bar.

**Whitelist guard** — `hybrid_search_orchestrator.py:193-228` (construction) and `379-384` (application): union of `is_code_whitelist.json` (33,557 canonical codes on disk) and every code live in `standards_registry` (33,564) at orchestrator start-up. Anything not in this set never reaches the reranker.

**Relevance confidence floor** — `hybrid_search_orchestrator.py:429-433`: post-rerank candidates scoring `<0.38` are dropped unless they're a verified direct code match.

**Edition resolver's states** — `edition_resolver.py:66-128`. `resolve()` returns exactly **4** possible `state` values, not 3: `no_edition_data` (code has no parseable year — applies to 40.0% of the registry, see Section 2), and, for codes that do have a year, one of 3 substantive states — `later_edition_exists` (a strictly newer dated edition of the same exact code exists), `restructured_edition_exists` (a newer *Part*-structured edition of the same root code exists), or `latest_in_registry` (nothing newer found). If the task brief's "three states" means the three that apply once a year is present, that's accurate; if it means the total count of distinct `state` values the function can return, the correct number is 4.

### Remaining hardcoded IS codes / material terms / product strings in the scoring path

The task brief specifically flags `hybrid_search_orchestrator.py:136-142` as an example location. **As the file exists in this checkout, that exact range (136-142) is the bilingual-demotion penalty block** (`score -= 0.25` for `"(b)"` in doc text, see Stage A table above) — it does not itself contain a hardcoded IS code. Read literally, the concrete hardcoded IS-code/material literals in the scoring path are:

- `hybrid_search_orchestrator.py:107` — `cement_grades = {"33grade", "43grade", "53grade"}`
- `hybrid_search_orchestrator.py:125` — `"1489" in is_code` (calcined-clay PPC Part 2 disambiguation)
- `hybrid_search_orchestrator.py:130` — `"1489" in is_code` (fly-ash PPC Part 1 disambiguation)
- `hybrid_search_orchestrator.py:165` — `"ductile"` hardcoded guard term
- `hybrid_search_orchestrator.py:139-143` — a fixed 15-word stop-list used for title-overlap scoring
- `query_preprocessor.py:97-325` — **`DOMAIN_SYNONYMS`, 228 lines, ~120 hand-mapped trade/Hindi/Hinglish terms to specific IS codes** (`IS 694`, `IS 1417`, `IS 1786`, `IS 269`, `IS 1489`, `IS 8112`, `IS 12269`, `IS 4151`, `IS 1893`, `IS 10500`, dozens more). This is by far the largest hardcoded component feeding retrieval — it runs *before* dense/lexical search on every query, injecting these exact code strings into the BM25-expanded query and, if the query is Indic/Hinglish, into the dense-encoded text too.
- `query_preprocessor.py:328-342` — `MATERIAL_GROUPS`, 13 hardcoded material-disambiguation buckets.
- `query_preprocessor.py:468-477` — hardcoded lithium/nickel/calcined-clay/fly-ash/fitting part-number inference rules.
- `query_preprocessor.py:580-584` — hardcoded `"calcined_clay"`/`"fly_ash"` conflict guards against the government-schedule matcher.

A note on what's *not* in this list any more: `hybrid_search_orchestrator.py:78-82` contains a comment recording that a `MATERIAL_SPECIFICITY_REGISTRY` — ten more hardcoded IS numbers keyed to test-set phrasing — **was deliberately removed** after an ablation showed it bought zero accuracy while pushing a wrong answer to the 0.999-clamp HIGH-confidence band. The comment is candid about why; the removal is real (grepped, no trace of the named registry remains).

### CRAG claims vs what's actually wired in

`retrieval/corrective_evaluator.py`'s docstring claims three CRAG capabilities: (1) retrieval confidence grading, (2) knowledge-strip extraction, (3) allied-graph fallback. Checked live this session:
- **(2) is real and wired in**: `extract_knowledge_strip()` is called from `hybrid_search_orchestrator.py:492-499` on every hit.
- **(1) `grade_confidence()` is dead code** — defined (`corrective_evaluator.py:143-155`) but called nowhere else in the repository (`grep` confirms only its own definition line). Confidence is graded solely by the single `get_confidence_band()` function above.
- **(3) `get_allied_fallback()` is dead *and* broken** — also called nowhere, and if it were called it would raise: it queries columns `target_standard`/`source_standard`/`frequency`/`edge_type` (`corrective_evaluator.py:169-173`) that do not exist in `allied_standards_edges` (real columns: `target_is_code`, `source_is_code`, `relation_type`, `relation_label`, `is_normative` — confirmed by running the exact query against the live DB, which raised `no such column: target_standard`). Its bare `except Exception: return []` would silently swallow that error if it were ever invoked.

### Rerank pool is 3 on this hardware, not 25

`auto_clamp_rerank_pool()` (`cross_encoder_reranker.py:22-55`) is meant to scale the cross-encoder candidate pool to available hardware. Measured live this session: `auto_clamp_rerank_pool(25)` → **3**, with no `RERANK_K`/`RERANK_K_NO_AUTO` override set anywhere in `.env` or the environment. On this CPU-only machine, only the **top 3** RRF-fused candidates ever reach the cross-encoder — the requested 25-candidate pool the constructor asks for (`hybrid_search_orchestrator.py:178`) is clamped down by 88% before reranking runs. (The function also contains obviously-dead code: lines 47-51 compute `clamped = min(requested_k, 6)` and then immediately overwrite it with `clamped = min(requested_k, 3)` on the next line, and lines 54-55 do the same in the `except` branch — the `6` branch can never execute.)

### Also see Section 4 (below) for: an OpenMP thread-safety issue that crashes the server on its first live query when launched by the project's own documented "Option B" instructions — that is a runtime/stability finding, not a scoring-logic one, but it directly gates whether any of the above ever executes at all outside the officially recommended launcher.

---

## SECTION 4 — Measured performance

Everything below was produced in this session by `backend/bench_live.py` against a single, freshly-started server instance (launched `OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE`, matching the project's own working launcher — see the crash finding immediately below for why that env var is not optional). Full raw console output is preserved at the paths cited; nothing here is re-derived from an earlier run or from README.

### Server stability — reproduced live, 2/2, before any accuracy numbers could be collected

Following `backend/README.md:209-213`'s own documented **"Option B: Running FastAPI Directly with Uvicorn"** instructions verbatim (`cd backend && uvicorn src.api.fastapi_application:app --host 127.0.0.1 --port 8000`) and then sending exactly one `/search` request:

- Attempt 1: server accepted the request, then the process disappeared mid-request (`RemoteDisconnected: Remote end closed connection without response`) after ~4.9s, with **no Python traceback** in the log — only a `multiprocessing/resource_tracker.py` "leaked semaphore" warning, the signature of an abnormal (non-Python-exception) process termination.
- Attempt 2: repeated from a clean process start. **Identical failure**, same symptom, same timing window.
- RSS was monitored through a third attempt: memory climbed from ~880MB to ~1.18GB over about 5 seconds of request handling, then the process vanished between two 0.3s-spaced samples — consistent with a crash during active model inference, not a graceful shutdown.
- No macOS crash report was generated in `~/Library/Logs/DiagnosticReports/` for either attempt, and `log show` without `sudo` surfaced nothing conclusive — root cause is **UNVERIFIED at the OS level**, but strong circumstantial evidence points to an OpenMP runtime conflict between PyTorch's and FAISS's bundled OpenMP libraries: `hybrid_search_orchestrator.py:10` already sets `KMP_DUPLICATE_LIB_OK=TRUE`, a known partial workaround for exactly this class of crash on macOS, and it was insufficient alone.
- **Confirmed fix**: launching with `OMP_NUM_THREADS=1` (in addition to `KMP_DUPLICATE_LIB_OK=TRUE`) prevents the crash — this is exactly what the project's own intended launcher does (`start.py:9-11`, `start.bat:7-8`, both comment "Prevent OpenMP runtime conflict segfaults between FAISS and PyTorch"). With that env var set, the same query that crashed the server twice succeeded reproducibly.
- **The cost of the fix**: single-threaded OpenMP makes inference slow. The first successful query after applying the workaround took **9.96s server-reported / 10.01s wall-clock** for one query — see the latency numbers below, all of which are necessarily measured under this same single-threaded workaround, because without it the server cannot complete a single query.

**This is a genuine, reproducible landmine for a judge**: `backend/README.md` documents Option B as a supported way to run the backend, with no mention anywhere in its own Troubleshooting section (`backend/README.md:366-381`) of this crash or the required env var. Anyone following that documented path gets a silent crash on their very first query with no diagnostic to act on.

All numbers below were collected against a server launched the *working* way (`OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE`, matching `start.py`), confirmed via `/health` returning `{"status":"healthy","offline_ready":true,"models_loaded":true}` before any measurement began, per the run's own harness (`backend/bench_live.py`), which exits non-zero on any per-query error and prints `INVALID RUN` if so (it did not, this run).

### 25 benchmark queries

Source: `backend/datasets/national_evaluation_test_set.json` (15) + `backend/datasets/public_test_set.json` (10) — the only two labelled query sets shipped in this repo, both authored by the same team that built the system. `top_k=5` used throughout.

| | |
| :--- | :--- |
| **CORRECT** | 21 |
| **INCORRECT** | 4 |
| **ERROR** | 0 |
| **NOT_RUN** | 0 |
| **Top-1 accuracy (denominator = 25 returned)** | **21/25 = 84.0%** |

**This is materially different from the `README.md` badge, which currently claims 100% Hit@1 on these exact two files.** That badge is stale against this checkout; do not quote it without re-running `bench_live.py`.

**Full top-1 score distribution (n=25, sorted):** `0.859, 0.8608, 0.9716, 0.972, 0.9818, 0.9823, 0.9893, 0.99, 0.9907, 0.9986, 0.999 ×15`

**Clamped at 0.999:** 15/25 (60.0%) — but **2 of those 15** are the wrong answer (see below). The 0.999 ceiling does not imply correctness.

**Lowest correct score:** 0.8590 (`PUB-09`, correctly returned `IS 6909: 1990`).

**Correct answers scoring below 0.75:** 0/21 — every correct answer in this run cleared the HIGH band; the benchmark's 4 failures are all wrong-answer failures, not low-confidence-but-right ones.

**The 4 incorrect answers, in full:**

| ID | Query (topic) | Expected | Got | Score | Read |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `NAT-12` | (mineral/material spec) | `IS 814` family | `IS 5206` | 0.9716 HIGH | Wrong standard, high confidence |
| `NAT-14` | (jute bags) | `IS 12650` family | `IS 16186: 2014` | **0.9990** HIGH | Wrong standard, clamped-max confidence |
| `PUB-03` | precast concrete pipes | `IS 458: 2003` | `IS 458: 2021` | 0.9990 HIGH | **Same base standard, newer edition than the test set's ground truth** — arguably a stale test label rather than a retrieval error, but scored strictly INCORRECT since it doesn't match the pinned expected string |
| `PUB-04` | lightweight concrete blocks | `IS 2185 (Part 2): 1983` | `IS 2185 (Part 1): 2005` | 0.9986 HIGH | Wrong **part** of the right base standard — a genuine multi-part disambiguation failure |

**n=25 on a self-authored set is not a general accuracy claim.** It says nothing about the other ~33,500 standards not represented in these 25 queries, or about phrasings the authors didn't anticipate — see the demo and out-of-domain results below, which use different phrasing and show a materially different picture.

### The demo queries (15 — see Section 2/note below on "9")

The task brief asks for "the 9 demo queries." No set of exactly 9 exists anywhere in the current codebase (`grep`-verified repo-wide). What exists and is actually shipped to users is the **15-query landing-page chip set** across 4 categories in `frontend/src/components/SpecSearch.jsx:7-32` — all 15 were run live:

| Category | Query (truncated) | Top-1 | Score | Band | match_quality | QCO | Edition state |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| PRODUCT | PVC cables 1100V | `IS 694: 2010` | 0.9575 | HIGH | confident | ✅ | latest_in_registry |
| PRODUCT | 22K gold hallmarking | `IS 1417: 2016` | 0.9441 | HIGH | confident | ✅ | latest_in_registry |
| PRODUCT | TMT Fe 500D | `IS 1786: 2008` | 0.9990 | HIGH | confident | ✅ | latest_in_registry |
| PRODUCT | drinking water | `IS 10500: 2012` | 0.9079 | HIGH | confident | ✅ | latest_in_registry |
| PRODUCT | PPC flyash cement | `IS 1489: 2019` | 0.9990 | HIGH | confident | ❌ | latest_in_registry |
| SPEC | CPWD RCC M25 work | `IS 456: 2000` | 0.8149 | HIGH | confident | ❌ | latest_in_registry |
| SPEC | MES 415V LT panel | `IS 14131` | 0.6307 | MEDIUM | uncertain | ❌ | **no_edition_data** |
| SPEC | DoCA 22K gold medals | `IS 1417: 2016` | 0.6653 | MEDIUM | uncertain | ✅ | latest_in_registry |
| MULTILINGUAL (Hindi) | पीवीसी तार 1100V | `IS 694: 1990` | 0.7598 | HIGH | confident | ✅ | **later_edition_exists** |
| MULTILINGUAL (Hindi) | 22K सोना हॉलमार्किंग | `IS 1417: 2016` | 0.8229 | HIGH | confident | ✅ | latest_in_registry |
| MULTILINGUAL (Hindi) | पीने का पानी परीक्षण | `IS 10500: 2012` | 0.7591 | HIGH | confident | ✅ | latest_in_registry |
| MULTILINGUAL (Hinglish) | bijli ke taar 1100V | `IS 694: 2010` | 0.7953 | HIGH | confident | ✅ | latest_in_registry |
| NATURAL | fire safety schools | `IS 1641: 1988` | 0.9990 | HIGH | confident | ❌ | **later_edition_exists** |
| NATURAL | drinking water test methods | `IS 3025 (Part 11): 1983` | 0.9990 | HIGH | confident | ❌ | latest_in_registry |
| NATURAL | rooftop solar inverters | `IS 16221 (Part 2): 2015` | 0.6990 | MEDIUM | uncertain | ✅ | latest_in_registry |

**11/15 HIGH/confident, 4/15 MEDIUM/uncertain, 0/15 rejected or errored.**

Two results are worth flagging on their own: the Hindi PVC-cable query (`पीवीसी तार 1100V`) returned **`IS 694: 1990`** — the *older* edition — correctly flagged `later_edition_exists`, while the Hinglish phrasing of the same intent (`bijli ke taar 1100V`) returned **`IS 694: 2010`**, the current one. Same underlying need, two different phrasings, two different editions surfaced — a concrete, live demonstration of both the edition-currency gap (Section 2/6) and the system's phrasing-sensitivity. The fire-safety query shows the same pattern (`IS 1641: 1988` returned, `later_edition_exists` flagged).

### Out-of-domain probes

8 probes run (NASA, biryani recipe, `IS 99999999`, React/Vite, income-tax filing, "capital of France," a coding request, a cricket-schedule request):

| Probe | Result | Read |
| :--- | :--- | :--- |
| `IS 99999999: fictional standard...` | 0 hits, `no_match` | Correctly rejected — whitelist/direct-code guard works |
| React vs Vite tooling | 0 hits, `no_match` | Correctly rejected |
| Capital of France | 0 hits, `no_match` | Correctly rejected |
| Reverse a linked list (Python) | 0 hits, `no_match` | Correctly rejected |
| IPL 2026 cricket schedule | 0 hits, `no_match` | Correctly rejected |
| NASA Mars rover thermal protection | 3 hits, top `IS 17941: 2022` ("Handpump cum Solar Pumping System"), 0.6801 **MEDIUM**, `uncertain` | Near-domain false positive — no real topical link to the top hit; matches `README.md`'s own disclosed behaviour that aerospace-adjacent queries aren't gated out, reproduced independently here with a different exact query string |
| **"best recipe for chicken biryani"** | 2 hits, top **`IS 13165: 1991` — "MEAT AND MEAT PRODUCTS - MUTTON BIRYANI (CANNED)"**, 0.5803 MEDIUM, `uncertain` | A real BIS standard for canned biryani exists, so the match is topically explicable, but the *query intent* (a recipe request) has nothing to do with a packaged-food quality standard — the gate doesn't distinguish "a standard mentions this food" from "this is a procurement question." The project's own narrower 4-probe test (`test_wrong_queries.py`) uses different exact wording ("Hyderabadi biryani recipe with basmati rice and saffron") and gets 0 hits — this run shows the gate is sensitive to exact phrasing, not just topic. |
| **"how to file income tax returns online in India"** | 3 hits, top `IS 19000: 2022` ("Online Consumer Reviews — Principles and Requirements"), 0.5800 MEDIUM, `uncertain` | A genuine false positive — a lexical/semantic collision on "online," no defensible topical link at all |

**5/8 cleanly rejected, 3/8 returned plausible-looking but wrong or borderline results — always at MEDIUM/`uncertain`, never HIGH/`confident`.** The relevance gate is not a hard guarantee, and this run found real, reproducible false positives beyond what the project's own narrower 4-probe out-of-domain test (`README.md`, `test_wrong_queries.py`) currently exercises. A UI or downstream system that respects `match_quality` stays safe from these; one that only reads the top hit's `is_code` would not.

### Latency

**Cold start** (process launch → first `/health` returning `models_loaded: true`, polled at 0.5s resolution): **21.97s**, this session's official-launch-path measurement (`OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE`). A second, independent cold-start measurement earlier in this session (before adding the OpenMP fix, different process) took 23.73s from a from-scratch process launch. Both are single-sample measurements on one machine — not averaged over multiple runs.

**First query** (first `/search` call against a freshly-ready instance, isolated from all other traffic): **9.961s server-reported / 10.014s wall-clock**, measured on a dedicated clean instance in this session as part of the crash-reproduction test.

**20 consecutive searches**, fixed identical query, same instance used for the 25+15+8 queries above (so already "warm" in every sense except repeating this exact query for the first time):

```
run  1: 10.662s   run  6: 5.039s   run 11: 2.736s   run 16: 1.142s
run  2:  5.759s   run  7: 6.196s   run 12: 1.797s   run 17: 1.179s
run  3:  5.020s   run  8: 4.328s   run 13: 1.451s   run 18: 1.140s
run  4:  5.797s   run  9: 5.702s   run 14: 1.259s   run 19: 1.147s
run  5:  4.287s   run 10: 3.859s   run 15: 1.149s   run 20: 1.179s
```

**min = 1.140s, median = 3.298s, max = 10.662s** (n=20, 0 crashes/errors).

The pattern is a clean, monotonic-ish decay from ~10s down to a stable ~1.14–1.18s plateau by run ~15, not random jitter. `encode_query_cached()` (`bge_multilingual_embedder.py`, `@lru_cache(maxsize=512)`) plausibly explains part of the drop — this exact query's dense embedding is only computed once, on run 1 — but that alone doesn't explain the continued decline from run 2 (5.76s) through run 15 (1.15s), since the cache should already be hot after run 1. The remaining mechanism is **UNVERIFIED**; it would be settled by adding per-stage timing instrumentation (dense search / BM25 / rerank / enrichment split out), which does not currently exist anywhere in this codebase (`ARCHITECTURE_AND_MODELS_GUIDE.md` itself says as much for BM25/FAISS: "No per-stage timing instrumentation exists").

**Stability across the 20 runs: 0 crashes, 0 errors** — confirms the `OMP_NUM_THREADS=1` workaround is durable under repeated load, not just a one-off fix for a single request.

### Addendum: testing against real, non-synthetic documents

Per an explicit request not to rely on any dummy/demo data, four real documents were sourced this session from legitimate public sources — two real government tender PDFs (not the repo's own synthetic `sample_compliant_tender.pdf`/`sample_missing_tender.pdf`), and two real official Indian Standard PDFs from `archive.org`'s `gov.in.is` collection (the same source this project's own ingestion pipeline uses).

**Real vs. template scope text, side by side.** This directly tests the Section 2 finding that 98.2% of the registry's `scope` field is a generated template. The real scope clause was extracted from the actual PDF (`archive.org/details/gov.in.is.269.2013`, page 3, "1 SCOPE") and compared against what the live database stores for the same standard family:

| Source | Text |
| :--- | :--- |
| Real PDF, `IS 269: 2013`, clause 1 | "This standard covers the manufacture and chemical and physical requirements of 33 grade ordinary Portland cement." |
| DB, `IS 269: 1989` (hand-curated, non-template) | "Covers the manufacture and chemical and physical requirements of 33 grade ordinary Portland cement." |
| DB, `IS 269` (undated, auto-generated) | "Indian Standard specification IS 269 covering requirements, dimensions, technical properties, sampling, and quality criteria for Specification for Ordinary Portland Cement, 33 Grade under Civil Engineering (CED)." |

The hand-curated row is essentially a verbatim match to the real standard's own scope clause — the curated 1.8% of the registry really is accurate, not just "not template." The auto-generated row confirms the opposite: generic, content-free boilerplate that repeats the title back with no information the title didn't already carry. Same pattern held on a second check against `IS 456: 2000` (the real PDF's clause 1.1 — "deals with the general structural use of plain and reinforced concrete" — matches the DB's curated entry's opening clause almost verbatim, while the DB's undated `IS 456` entry is the same generic template).

**Tender-audit against two real government tenders.** Both PDFs came from official `.ac.in` institutional domains (IISER Kolkata, 55 pages; IIT Kanpur, 115 pages) — real, currently-live public-works tenders, not samples. Both runs surfaced the same pattern:

- `items_parsed` came back as exactly **40** for both documents, despite being very different lengths (55 vs. 115 pages). Traced to source: `tender_document_parser.py:296-297` silently caps extraction at `boq_items[:20]` + `technical_clauses[:20]` — **a second, previously undocumented truncation point**, upstream of the `MAX_AUDIT_ITEMS=10` scoring cap already covered in Section 6. The `items_parsed` field the API reports reflects this already-truncated count, not the document's true total — a caller cannot tell from the response alone whether a document had 40 real items or 400.
- On both real documents, all 10 items that made it through the scoring cap were **administrative/procedural boilerplate** — bid eligibility, tender-fee deposits, site-visit advisories, contractor enlistment rules — not technical material specifications. Every one scored `NO_CONFIDENT_MATCH` (the fail-closed default), several paired with an IS-code suggestion that has no clear relevance to the sentence it was matched against (e.g. a tender-fee-deposit clause matched to `IS 5898: 1970`). This is the safe behavior — it never claims false compliance — but on tenders shaped like these two genuine ones, the technical Bill-of-Quantities content (if present at all in the PDF, as opposed to a separate BoQ attachment) is never reached: the 20-item parse cap plus the 10-item audit cap are consumed entirely by front-matter before any real material specification is assessed.

This is a materially different and more specific finding than the generic "item cap" limitation already in Section 6 — the synthetic sample PDF used for the earlier Section 5 demonstration is short enough (4 parsed items) that this two-stage truncation never became visible. Real tenders are long enough that it does.

### Addendum: parser selection fixed and re-verified against the same real documents

**Root cause, precisely:** `tender_document_parser.py:296-297` (before the fix) sliced `boq_items[:20]` and `technical_clauses[:20]` in document order. Real tenders front-load administrative content (bid eligibility, EMD, submission terms), so on both real documents above, the first 20+20 extracted items were dominated by front-matter, and the first-20-in-order slice never reached the technical specification section at all.

**Fix implemented — select, don't truncate.** Both caps stay at 20 (unchanged); what changed is which 20 get kept. A new `technical_relevance_score()` (`tender_document_parser.py`) ranks every item that has already survived the existing `is_pure_boilerplate()` filter, and `select_top_by_technical_score()` stable-sorts by that score (descending, ties keep document order) before slicing. The scoring rule:

| Signal | Points | Pattern |
| :--- | :---: | :--- |
| Material/product noun | +2 | cement, steel, TMT, cable, pipe, valve, transformer, paint, tile, brick, ... (~40-term list) |
| Quantity with a construction/BOQ unit | +2 | `cum`, `sqm`, `kg`, `MT`, `nos`, `running metre`/`rmt`, `litre` |
| IS code citation | +2 | `\bIS[\s:]*\d{2,6}\b` — deliberately case-sensitive on capital "IS" to avoid matching the copula "is" followed by an unrelated number (e.g. "the estimated cost is 617136") |
| Grade or dimension | +2 | `M25`-style, `Fe 500`-style, `NN grade`, `NN mm`, `NN kV` |
| Administrative keyword (each match) | −3 | EMD, earnest money, eligibility, bid security, tender fee, affidavit, undertaking, GST registration, turnover, completion certificate, arbitration, penalty clause |

This only re-ranks; it never drops an item the existing filter would have kept anyway, and it makes no change to retrieval, scoring, thresholds, the QCO engine, or the four audit states.

**Re-verified live against the same two real tenders**, freshly re-uploaded to a restarted server running the new code:

| | IISER Kolkata (55pp) | IIT Kanpur (115pp) |
| :--- | :---: | :---: |
| `items_parsed` | 40 (unchanged — parser cap is still 20+20) | 40 (unchanged) |
| Items scored (of the 10-item audit cap) | 10 | 10 |
| **Technical line items** (vs. administrative) | **10/10** | **9/10** (one borderline site-security/watch-and-ward clause) |
| Matched to an IS code | **10/10** | **10/10** |
| Triggered `QCO_REQUIRED` | 2/10 (cement QCO) | 0/10 |
| `STANDARD_SUGGESTED` | 1/10 | 0/10 |
| `NO_CONFIDENT_MATCH` | 7/10 | 10/10 |
| `COMPLIANT` | 0/10 | 0/10 |

Both comfortably clear the 6/10 technical-content bar this fix was built against — IISER's audited items now read as real BoQ lines ("Providing, fitting, fixing and fabricating (ISI) marked Heavy Duty MS IR Filter Vessel...", "Supplying fitting and fixing of 80 NB MS Frontal Pipeline (ISI) with 5 Nos Butterfly Valve...") instead of "the bid document consisting of Plans, Specifications..."-style front-matter. Most items still land on `NO_CONFIDENT_MATCH` rather than `COMPLIANT`/`QCO_REQUIRED` — that's the retrieval confidence gate working as designed on genuinely hard, terse BoQ phrasing, not a parser problem, and it's out of scope for this fix per the guardrails (no retrieval/scoring changes).

**Regression checks, all passed:** `sample_missing_tender.pdf` and `sample_compliant_tender.pdf` re-run — identical `items_parsed` (4 each) and identical per-item verdicts to before the fix (2 `NO_CONFIDENT_MATCH` / 2 `COMPLIANT` respectively). The 25-query benchmark re-run — identical `21/25 (84.0%)` with an identical score distribution (this endpoint never touches the tender parser, so this was expected, and confirmed). Zero DB writes this pass.

---

## SECTION 5 — Requirements

Scored against PS 26108's 7 "Expected Features" as quoted in Section 1 (1 = portal integration, drawn from the Description line; 2–7 = the six explicit bullets). Every IMPLEMENTED or PARTIAL verdict below is backed by a live call made in this session (Section 4, plus two additional live checks run specifically for this section).

### 1. Integrate with procurement portals — **ABSENT**
`/gem-clause` (`fastapi_application.py:309-314` → `gem_specification_generator.py`) produces clause text only — live-tested this session (`IS 1786: 2008` → a 4-clause tender specification text block, including an edition-currency disclaimer clause). `README.md:218-222` already discloses "does not transact with GeM, CPPP or GePNIC." No HTTP client, credential handling, or catalogue-lookup code for any procurement portal exists anywhere under `backend/src/` (repo-wide search, zero matches). **Gap a hostile evaluator would find:** ask to push a generated clause into a live GeM tender — nothing in the system can do that; output must be copied by hand.

### 2. Accept product descriptions, technical specifications, or tender documents as input — **IMPLEMENTED**
`/search` accepts free text — demonstrated 48 times live this session (25 benchmark + 15 demo + 8 OOD queries, Section 4, 0 errors). `/tender-audit` accepts PDF/CSV — live-tested this session against `backend/sample_missing_tender.pdf`: real PyMuPDF extraction found 4 parseable items, 2 were audited (both `NO_CONFIDENT_MATCH` — the fail-closed default when retrieval confidence isn't HIGH, not a false "compliant"). **Gap:** the PDF path caps assessment at 10 items by default (`MAX_AUDIT_ITEMS`, Section 6) and the live test's own `audit_truncated: true` flag shows 2 of the 4 parsed items never reached an audit verdict at all (a dedup/technical-clause-limit interaction, not the 10-item cap in this particular case, since only 2 items were processed).

### 3. Recommend standards by semantic understanding rather than keyword matching — **PARTIAL**
BGE-M3 + FAISS genuinely drive part of ranking, demonstrated live at 84.0% (21/25) top-1 accuracy (Section 4). But retrieval is a hybrid of dense embeddings, BM25, and a 228-line hand-authored keyword-to-IS-code dictionary (`DOMAIN_SYNONYMS`, Section 3) that runs *before* either retriever and materially shapes what both see — e.g. the Hindi/Hinglish demo queries only resolved correctly because `DOMAIN_SYNONYMS` bridges them to English BIS vocabulary, not because BGE-M3 alone mapped Hindi text to the right English-titled standard. **Gap:** "rather than keyword matching" overstates the design; it is semantic search heavily assisted by keyword mapping, not a replacement for it.

### 4. Identify allied standards (normative, test, terminology, safety, installation, related-product) — **PARTIAL**
`AlliedStandardsClassifier` implements exactly this six-way taxonomy, and it's real: live-tested this session on `IS 456: 2000` (returned by the CPWD-RCC demo query) — **13 allied edges returned**, correctly typed (`IS 516: 1959` as `NORM_TEST`, `IS 1786: 2008` as `RAW_MATERIAL`, etc.). But coverage is 157/33,564 source codes (0.47%, Section 2), hand-authored rather than parsed from each standard's own normative-references clause. **Gap:** ask for allied standards on most of the other 20 correct benchmark hits (e.g. `IS 269: 1989`, `IS 383: 1970`) and — untested per-code here, but consistent with the 0.47% coverage figure — the great majority will return nothing, with no signal distinguishing "not covered" from "genuinely has no allied standards."

### 5. Highlight latest version and amendments — **PARTIAL**
`EditionResolver` genuinely computes a live per-hit edition state — demonstrated 3 different real states occurring across the 15 demo queries alone (`latest_in_registry`, `later_edition_exists` ×2, `no_edition_data` ×1, Section 4). But `amendments_count` is 99.86% constant zero (Section 2) — not real amendment tracking — and this session's own demo run surfaced a live, concrete example of the gap the mechanism can't close: the Hindi PVC-cable query returned `IS 694: 1990` (correctly flagged `later_edition_exists`) while the Hinglish phrasing of the same need returned the current `IS 694: 2010` — the "latest version" isn't consistently what gets recommended even when the resolver knows a later one exists.

### 6. Suggest mandatory certification requirements (ISI/CRS/Hallmarking) — **IMPLEMENTED for its covered set; PARTIAL overall**
`QCOMandatoryEngine` + 759 real, government-sourced QCO rows (Section 2) — demonstrated live: 10/15 demo queries and most cement/steel/water/gold benchmark queries carried a real `qco_rules` payload (e.g. gold hallmarking, TMT steel, PVC cables all showed `qco_present=True`). Where covered, this is solid, well-sourced data (Section 7). **Gap:** coverage is ~1.7–2.0% of the full registry (Section 2); anything outside the 759 defaults to "voluntary" (`qco_mandatory_engine.py:41-52`) — a false negative on a legal obligation, which is precisely the failure mode this feature exists to prevent.

### 7. Support multilingual input and natural-language queries — **IMPLEMENTED**
Demonstrated live this session: 4 Hindi/Hinglish demo queries (Section 4) all returned real, on-topic HIGH-confidence results; natural-language boilerplate stripping (`query_preprocessor.py:45-94`) is real regex logic, not a stub, and processed all 3 `NATURAL` category demo queries correctly. The PS asks specifically for *input* support, which is what's implemented and verified; multilingual *output* is a separate, much weaker claim (Section 6) that this specific requirement does not cover as literally worded.

**Summary: 1/7 fully IMPLEMENTED (multilingual input), 1/7 IMPLEMENTED-but-capped (input formats, PDF/CSV), 3/7 PARTIAL (semantic-purity, allied standards, edition/amendment currency), 1/7 IMPLEMENTED-for-a-small-slice (QCO), 1/7 ABSENT (portal integration). Zero features are fully implemented with no caveat.**

---

## SECTION 6 — Limitations

Every number here was measured in this session (Section 2 for data-side figures, Section 4 for runtime ones); none is carried over from `README.md`.

| Limitation | Measured | Practical meaning | What closing it requires |
| :--- | :--- | :--- | :--- |
| **Server crashes on first query under documented launch instructions** | Reproduced 2/2 via `backend/README.md`'s own "Option B" (Section 4); 0/20 crashes once `OMP_NUM_THREADS=1` is set | Anyone running the backend the way the backend's own README says to gets a silent crash with no diagnostic | Either fix the underlying OpenMP conflict in code (so `OMP_NUM_THREADS=1` isn't load-bearing for basic stability), or add the missing env var to Option B's documented command and to the Troubleshooting section |
| **Edition currency** | Registry is a static snapshot, `MAX(created_at)`=2026-09-10; 40.0% undated; 1,738 multi-edition base codes tracked; only 16/33,564 (0.05%) supersession links, 11 of those 16 wrong; 3 specific stale-ACTIVE examples live-verified this session (`IS 516: 1959`, `IS 694: 1990`, `IS 12269: 1987`) | System will confidently present an outdated edition as current for any unlinked pair — reproduced live in Section 4/5 (the Hindi PVC-cable query) | A live BIS catalogue feed or licensed edition register; the current archive.org mirror carries no supersession feed to build one from |
| **Allied standards coverage** | 157/33,564 source codes (0.47%), hand-authored, not parsed from source citations | Feature returns nothing for >99% of standards, with no signal distinguishing "not covered" from "none exist" | Licensed access to each standard's actual Normative References clause, or a much larger sourced citation dataset |
| **QCO coverage** | 759 products, ~575–663 tie to the registry (~1.7–2.0% of 33,564) | A product outside the 759 defaults to "voluntary" — a false negative on a legal obligation | The full current BIS Scheme-I/II/IV gazette list, not just the ~760 already scraped |
| **Multilingual output** | 12/33,564 codes (0.036%) have real curated translations across 7 languages; all others show an English scope excerpt in a template sentence, with the title explicitly marked untranslated | Hindi-speaking officer gets correct results but English-language titles/scopes for 99.96% of standards | A real translation pipeline with domain QA, or substantially more hand-curation — not query-side logic |
| **Procurement portal integration** | 0 integration code found anywhere in `backend/src/` (Section 5) | Clause text must be copy-pasted by the officer | GeM API credentials and an actual integration client |
| **Undated records** | 13,412/33,564 (40.0%) | No edition-currency checking possible for these at all | A source with reliable per-standard publication years |
| **Text-extraction / encoding artifacts** | 46/33,564 titles (0.14%) show mojibake from archive.org metadata; separately, 557/613 (90.9%) of the hand-curated `full_text` records carry raw page-header/footer noise inline (e.g. `"10.42\nSP  21 : 2005"`) from an unclean extraction of the `SP 21:2005` summary compendium | Any UI surface rendering `full_text` or these titles verbatim shows the noise to a user | A text-cleanup pass (strip repeating header/footer patterns) — bounded and tractable, unlike the coverage gaps above |
| **Item cap on tender audit — two stages, not one** | `MAX_AUDIT_ITEMS=10` (`fastapi_application.py:209`) scores only the first 10 of what the parser extracted — but the parser itself already silently caps extraction at `boq_items[:20]` + `technical_clauses[:20]` (`tender_document_parser.py:296-297`), confirmed live this session against 2 real government tender PDFs (55pp and 115pp), both of which hit `items_parsed=40` exactly despite very different lengths | On real tenders (not the repo's short synthetic samples), all 10 scored items can be administrative boilerplate (bid fees, eligibility, site visits) rather than technical specifications — the real Bill-of-Quantities content may never be reached at all, and `items_parsed` reports the already-truncated count, not the document's true total | Raise or remove both caps, and prioritize likely-technical content (e.g. lines with units/quantities/material keywords) over document order when deciding what to keep — a code change, and one that also needs the OpenMP/latency fix first to stay usable at higher item counts |
| **Single-threaded concurrency** | **UNVERIFIED** as a throughput number — not load-tested this session | `/search` is a synchronous `def` endpoint (`fastapi_application.py:118`) dispatched to a worker thread by FastAPI, but inference is forced to `OMP_NUM_THREADS=1` to avoid the Section 4 crash, so concurrent requests likely serialize on CPU regardless of thread count | Firing several simultaneous requests at a live instance and measuring completion-time scaling — not attempted in this session given the time already spent on the crash investigation |

---

## SECTION 7 — What is genuinely strong

Only where evidenced this session:

1. **The honesty layer is real, not cosmetic.** `get_confidence_band()` is a single, consistently-applied threshold function (Section 3) — every confidence figure quoted anywhere in this report traces back to it. The frontend surfaces it as a badge and relevance label (`StandardCard.jsx`, direct-read confirmed); superseded standards get an explicit warning box (`StandardCard.jsx:193-220`); every result implicitly carries a provenance trail back to a live-computed snapshot date via `/api/registry-stats` (`fastapi_application.py:353-466`), which calculates its coverage percentages from the database at request time rather than hardcoding them.

2. **QCO data is genuinely government-sourced.** 710 Scheme-I rows carry real `bis.gov.in` gazette PDF URLs and S.O. notification numbers; 51 Scheme-II rows carry `crsbis.in` provenance (Section 2, verified live). Live-tested this session: gold hallmarking, TMT steel and PVC-cable queries all returned real, specific, correctly-scoped QCO warnings (Section 4/5). This is the best-sourced dataset in the system.

3. **FAISS/DB index alignment is exact.** 33,564 vectors for 33,564 registry rows, 1:1, confirmed by direct comparison this session — no silent drift between what's searchable and what's in the database.

4. **Offline operation holds up for the core path.** BGE-M3 and bge-reranker-v2-m3 run locally once cached; SQLite/FAISS/BM25 are local files; all 48 live queries in Section 4 ran with zero network dependency. The only network-touching paths (API Setu live gateway, cloud-LLM rationale) are both confirmed gated behind config that isn't set by default in this checkout (`apisetu_gateway.py`'s `is_live_configured`; the shipped frontend never sets `use_cloud_llm`).

5. **Multilingual input is real.** Demonstrated live, not asserted: 4/4 Hindi/Hinglish demo queries this session returned correct-domain results, 3 of them HIGH confidence (Section 4). This is a materially different, stronger claim than the multilingual-output limitation in Section 6, and it holds up under direct testing.

6. **The relevance gate mostly works, and its failures are legible, not silent.** 5/8 out-of-domain probes were cleanly rejected; the 3 that weren't never rose above MEDIUM/`uncertain` (Section 4) — a system respecting `match_quality` stays safe even on the probes this session found that the project's own narrower 4-probe test doesn't cover.

7. **The team has already self-corrected once, visibly.** `README.md`'s own "Known Limitations" section, the `MATERIAL_SPECIFICITY_REGISTRY` removal comment (`hybrid_search_orchestrator.py:78-82`, candid about why a hardcoded table was deleted after it proved useless), and the four-state fail-closed tender-audit design (Section 3) all show a working pattern of finding and disclosing overclaims rather than hiding them. This document extends that pattern; it does not start it from zero.

---

## SECTION 8 — Judge Q&A

Twenty questions, each answered from this session's own measurements with its evidence.

**1. Is this standard the current version?**
Not verifiably, in general. The registry is a static snapshot (ingested 2026-09-10) from an unofficial archive.org mirror with no supersession feed. Only 16/33,564 records (0.05%) carry a supersession link, and this session independently re-verified that 11 of those 16 are themselves wrong. This session also live-verified three specific standards (`IS 516: 1959`, `IS 694: 1990`, `IS 12269: 1987`) marked ACTIVE despite strictly newer editions of the same code sitting unlinked in the same database — and then reproduced the practical consequence live: a demo query returned `IS 694: 1990` as top-1. The UI's own advisory to verify at `standardsbis.bsbedge.com` is the actual safeguard.

**2. How do you know your data is accurate?**
Provenance varies sharply by field (Section 2), not uniform. QCO data is well-sourced (real gazette URLs, verified live). Standard identity comes from archive.org's catalogue metadata. But `scope` text is a generated template for 98.2% of records — not extracted from the standard itself — and `reaffirmation_year` for auto-harvested rows is just the publication year restated (99.7% of populated values). Nothing here is independently audited against BIS's own master catalogue.

**3. What happens on a query outside your domain?**
A relevance gate rejects it with zero hits if neither retriever clears threshold (Section 3). Live-tested with 8 probes this session: 5/8 cleanly rejected (`IS 99999999`, coding, trivia, cricket schedule, frontend tooling). 3/8 — a NASA-adjacent query, a biryani recipe, and an income-tax-filing question — returned MEDIUM-confidence, `uncertain` results rather than a hard rejection. None reached HIGH/`confident`. The gate is a filter, not a guarantee, and this session found real false positives beyond the project's own narrower published test set.

**4. Why is it not integrated with GeM?**
Because it was never built to be. `/gem-clause` generates copy-paste tender text; no GeM/CPPP/GePNIC API client exists anywhere in the repository (Section 5, confirmed by repo-wide search). Real integration needs GeM API access and a client — a separate, unattempted engineering effort.

**5. What is your accuracy, and on what sample?**
84.0% top-1 (21/25), measured live this session against the two benchmark files shipped in the repo — 15 self-authored "national" queries plus 10 self-authored "public" queries, n=25 total. This is materially lower than `README.md`'s current 100% badge, which is stale against this checkout. n=25 on a self-authored set says nothing about general accuracy across the other ~33,500 standards.

**6. Is any part of this hardcoded?**
Yes, extensively, and it's load-bearing, not incidental (Section 3 has the full inventory): a 228-line keyword-to-IS-code dictionary that runs on every single query, ~13 hardcoded material-disambiguation buckets, hardcoded cement-grade and part-number rules, and a 27-edge, 5-code hand-typed allied-standards table. Separately: the shipped database contains a `ground_truth_overrides` table (687 rows, `query_pattern → is_code`) with no schema entry in `schema.sql` and zero references anywhere in the application code (repo-wide `grep`, confirmed empty) — it currently affects nothing at runtime, but its presence in the shipped DB with no code path using it is worth asking the team about directly.

**7. What does this get wrong?**
In this session's own 25-query benchmark: 4/25 (16.0%). One wrong part-number (`IS 2185 Part 1` for an expected `Part 2` query). One wrong standard at 0.97 HIGH confidence. One wrong standard at the **0.999 confidence ceiling** — the system's maximum displayed confidence gave no warning it was wrong. One edition mismatch against the test set's specific pinned year (arguably a stale test label, not a retrieval miss). Separately, 3/8 out-of-domain probes returned plausible-looking but wrong results at MEDIUM confidence (Section 4).

**8. How fast is it?**
Cold start (process launch to healthy): 21.97s, this session. First live query on a clean instance: ~10.0s. 20 consecutive identical queries against an already-warm instance: min 1.140s, median 3.298s, max 10.662s — with a clear decay from ~10s down to a ~1.15s plateau across the run, not a flat number (Section 4). All of these are necessarily measured under the `OMP_NUM_THREADS=1` workaround; without it, the server does not complete a request at all (see Q11).

**9. What happens if I ask in Hindi?**
Tested live: 4/4 Hindi/Hinglish demo queries returned on-topic, correctly-domained results this session, 3 of 4 at HIGH confidence (Section 4). Titles and scopes in the response are in English for all but 12 of 33,564 standards (Section 6) — the query side genuinely understands Hindi; the answer content mostly doesn't come back translated.

**10. Does it work offline?**
Yes, for the core search path — confirmed by this session's 48 live queries, all served with no network calls beyond the already-cached local models. Two optional paths (API Setu live gateway, cloud-LLM rationale) need network and neither is enabled by default in this checkout.

**11. Can the server just... crash?**
Yes, reproducibly — this session found it crashes on the very first live query, 2/2 attempts, when launched exactly as `backend/README.md`'s own "Option B" instructions say to, with no traceback and no entry in the repo's own Troubleshooting section. The project's actual intended launcher (`start.py`) works around it with `OMP_NUM_THREADS=1`, at a real, measured latency cost (Q8).

**12. Can a procurement officer trust a "voluntary" QCO label?**
Not fully. QCO coverage is ~1.7–2.0% of the registry (Section 2/6); a product not in that set defaults to "voluntary" even if a real Quality Control Order applies. This is flagged as the single most consequential limitation in the system, by the codebase's own design comments as much as by this analysis.

**13. Why does confidence stay HIGH even when the answer is wrong?**
Confidence reflects retrieval/reranking signal strength — dense similarity, lexical overlap, cross-encoder score — not ground-truth correctness; there is no independent verification step. This session's own benchmark shows 2 of 4 wrong answers scored at the 0.999 ceiling, the system's maximum.

**14. How many Indian Standards does this actually cover?**
33,564 in the registry as shipped in this checkout — not the 33,748 `README.md` currently states (stale by 184 rows, measured this session). Of those, 40.0% have no parseable edition year and 98.2% carry generated rather than extracted scope text.

**15. What's the "knowledge strip" shown under each result?**
A single sentence extracted from the standard's scope text, scored by keyword/grade/material overlap with the query (`corrective_evaluator.py:80-140`) — real extraction logic, but for 98.2% of records it's extracting from a generated template sentence, not the standard's actual scope (Section 2).

**16. Does the system ever invent a standard that doesn't exist?**
The whitelist guard (Section 3) is specifically built to prevent this — every candidate is checked against the live registry before it can be returned. Live-tested this session: `IS 99999999` was rejected with 0 hits.

**17. What happens with a 50-item tender upload?**
Two truncation points, not one, both confirmed live this session. The parser itself caps extraction at 20 BoQ items + 20 technical clauses (`tender_document_parser.py:296-297`) before the API ever sees the document — verified against two real 55pp and 115pp government tenders, both of which hit exactly `items_parsed=40`. Of what survives that, only the first 10 get scored (`MAX_AUDIT_ITEMS`). On those same two real tenders, every one of the 10 scored items was administrative boilerplate (fees, eligibility, site visits) — the real technical content was never reached. `items_parsed` reports the already-truncated count, not the document's true total, so the officer can't tell from the response how much was actually dropped.

**18. Is the allied-standards graph complete for the standard I care about?**
Almost certainly not, unless it's one of the 157 codes it covers (0.47% of the registry) — and even for those, it's hand-curated, not derived from the standard's own cited normative references (Section 2/3). Live-tested: `IS 456` (a covered code) returned 13 real allied edges; most codes will return none.

**19. Why does GeM clause generation sometimes cite a different code than I asked for?**
Because `GeMSpecificationGenerator` resolves a superseded code to its current version before drafting (`gem_specification_generator.py:33`, via `StandardsLifecycleTracker`) — real logic, not cosmetic — though it inherits the same supersession-data gaps discussed in Q1.

**20. What would make this production-ready for real procurement use?**
At minimum: a live or licensed BIS catalogue feed for edition currency; a real GeM API integration; QCO coverage closer to the full statutory gazette list rather than ~760 items; and fixing the crash-on-first-query issue for anyone not using the project's own launcher script. All but the last require data partnerships this codebase alone cannot manufacture; the last is a code fix.
