# Indian Standards (BIS) Recommendation Engine

> **Offline-First AI Recommendation & Regulatory Compliance Engine for the Bureau of Indian Standards (BIS)**  
> Runs with no network once the BGE-M3 and bge-reranker-v2-m3 weights are cached locally. First boot downloads those weights from the Hugging Face Hub; the API Setu live gateway and the `use_cloud_llm` rationale path stay dormant unless API credentials are supplied.  
> Engineered for real-time tender specification auditing, mandatory Quality Control Order (QCO) enforcement, automated Government e-Marketplace (GeM) procurement clause generation, and cross-encoder precision search.

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Hit@1 Accuracy](https://img.shields.io/badge/Hit%401-84.0%25_(n%3D25)-yellow)](docs/SYSTEM_ANALYSIS.md)
[![Offline Capable](https://img.shields.io/badge/Offline-first-orange)]()

---

## Benchmark Performance Highlights

Measured live against a fresh backend instance (`backend/bench_live.py`, see [`docs/SYSTEM_ANALYSIS.md`](docs/SYSTEM_ANALYSIS.md) Section 4 for the full run): **21/25 (84.0%) top-1 accuracy, strict**, on the two self-authored benchmark files shipped in this repo (n=25 — this is not a general accuracy claim, and both files were written by the same team that built the system).

Of the 4 misses, one (`PUB-03`) is an outdated test label, not a retrieval error: the test expects `IS 458: 2003`, but the registry now also contains `IS 458: 2021` — the current edition of the exact same standard ("Precast Concrete Pipes") — and the system correctly recommends the current one. We do not edit test sets to raise the score, so it still counts as a strict miss. **Excluding that one label: 22/25 (88.0%).**

The other 3 misses are real: two of them (`NAT-12`, `NAT-14`) are the system confusing closely-related sibling standards at HIGH or maximum (0.999) confidence — e.g. recommending the *stainless-steel* welding-electrode standard for a *carbon-steel* electrode query. The fourth (`PUB-04`) is a wrong Part number on the right base standard. See `docs/SYSTEM_ANALYSIS.md` Section 4 for the full breakdown, including the full score distribution and confidence bands.

| Benchmark / Evaluation Suite | Queries Tested | Hit@1 (strict) | Hit@1 (excl. 1 stale label) |
| :--- | :---: | :---: | :---: |
| **Official National Benchmark** (`national_evaluation_test_set.json`) | 15 | **13/15 (86.7%)** | 13/15 (86.7%) |
| **Public Evaluation Test Set** (`public_test_set.json`) | 10 | **8/10 (80.0%)** | 9/10 (90.0%) |
| **Combined** | 25 | **21/25 (84.0%)** | **22/25 (88.0%)** |
| **Out-of-Domain Guard** (`backend/bench_live.py`, 8 probes) | 8 | — | 5/8 cleanly rejected; 3/8 returned MEDIUM-confidence false positives (see `docs/SYSTEM_ANALYSIS.md` Section 4) |

The out-of-domain guard is not a blanket guarantee. A near-domain aerospace-materials probe is not rejected — it returns results banded MEDIUM with `match_quality: uncertain`, the intended behaviour for a near-domain query. This session's own 8-probe run also found 2 genuinely out-of-domain queries (a food-recipe query, an income-tax-filing query) returning MEDIUM-confidence results rather than a clean rejection — see `docs/SYSTEM_ANALYSIS.md` for the exact probes and results.

---

## Core System Architecture

```
User Query / Government Tender (PDF/CSV) / Hinglish / Regional Indic
                              │
                              ▼
┌────────────────────────────────────────────────────────────────────────┐
│             Adaptive Query Preprocessor & Intent Classifier             │
│  - Strips tender legalese & boilerplate ("Notice Inviting Tender for")  │
│  - Disambiguates series sub-parts (IS 1239-2 fittings vs IS 1239-1)    │
│  - Detects engineering materials, grades, and Intent (Spec / Test / Code)│
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                  ┌────────────────┴────────────────┐
                  ▼                                 ▼
       ┌─────────────────────┐           ┌────────────────────┐
       │ Dense Semantic FAISS│           │ BM25 Lexical Index │
       │  BGE-M3 (1024-dim)  │           │ Technical Synonyms │
       └──────────┬──────────┘           └─────────┬──────────┘
                  │                                 │
                  └────────────────┬────────────────┘
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │   Zero-Hallucination Relevance Gate & OpenMP Runtime   │
       │   - Rejects out-of-domain / culinary queries (0 hits)   │
       │   - PyTorch OpenMP threadpool memory-harmonized        │
       └───────────────────────────┬────────────────────────────┘
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │        Hardware-Adaptive Cross-Encoder Reranker        │
       │   BAAI/bge-reranker-v2-m3 with dynamic hardware ladder  │
       │   Auto-clamps candidate pool on CPU (4-12s measured)   │
       └───────────────────────────┬────────────────────────────┘
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │       Domain-Adapted Local Corrective RAG (CRAG)       │
       │   - Deconstructs standards scope into knowledge strips │
       │   - Computes query-clause semantic relevance alignment │
       │   - Fallback to SQLite allied standards graph          │
       └───────────────────────────┬────────────────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
┌───────────────────────────┐             ┌───────────────────────────┐
│ Grounded Rationale Engine │             │ GeM Procurement Generator │
│ Factual explanation cited │             │ Mandatory QCO compliance  │
│ directly on CRAG strip    │             │ clause ready for tenders  │
└───────────────────────────┘             └───────────────────────────┘
```

---

## Key Features & Capabilities

### 1. Domain-Adapted Local Corrective RAG (CRAG)
- **Clause-Level Decompose-then-Recompose:** Standard scopes (which often span multiple pages with historical adoption boilerplate) are deconstructed into atomic clauses.
- **Knowledge Strip Extraction:** Evaluates clauses against query entities, material grades, and application cues to extract the exact, relevant factual sentence for grounding.
- **Graph Fallback:** Dynamically queries the SQLite `allied_standards_edges` graph if candidate confidence is ambiguous.

### 2. Multi-Part Series & Intent Disambiguation
- **Part Disambiguation:** Resolves complex multi-part series:
  - Steel Tubes (`IS 1239 Part 1`) vs Pipe Fittings (`IS 1239 Part 2`)
  - Lithium Secondary Cells (`IS 16046 Part 2`) vs Nickel (`IS 16046 Part 1`)
  - Calcined Clay PPC (`IS 1489 Part 2`) vs Fly Ash PPC (`IS 1489 Part 1`)
  - Seismic Detailing (`IS 13920`) vs General Earthquake Design Criteria (`IS 1893`)
- **Intent Alignment:** Differentiates between **Product Specifications** (e.g., `IS 8112`), **Methods of Test** (e.g., `IS 516`, `IS 4031`), and **Codes of Practice** (e.g., `IS 456`, `IS 800`).

### 3. Public Procurement & Tender Legalese Ingestion
- **Boilerplate Stripper:** Automatically removes procurement noise (`"Notice Inviting Tender for"`, `"The contractor shall ensure"`, `"Supply, delivery, laying, jointing and testing of"`).
- **CPWD DSR & GeM Integration:** Pre-compiled trie matches standard Central Public Works Department Schedule of Rates and Government e-Marketplace procurement descriptions.
- **Tender Document Parser:** Ingests and audits technical clauses from uploaded multi-page PDFs and CSV Bills of Quantities (BoQ).

### 4. Multilingual & Hinglish Support
- Handles regional Indian language **input** (**Hindi, Marathi, Tamil, Telugu, Bengali, Gujarati, Kannada**) and conversational Hinglish (`"RCC chhat ke water leakage ko rokne ke liye waterproofing compound"`, `"Makaan aur building slab dhalai Fe 500D grade sariya"`).
- Normalizes Devanagari numerals (`०-९`) to standard Arabic digits.
- **Output** translation is curated for 12 standards only; all other titles render in English and are marked as untranslated. See [Known Limitations → Multilingual output](#multilingual-output).
- **Output** translation is curated for 12 standards only. See [Known Limitations → Multilingual output](#multilingual-output).

### 5. Mandatory Quality Control Order (QCO) Enforcement
- Cross-references candidate standards with gazetted Quality Control Orders issued under the BIS Act, 2016.
- Flags legally mandatory standards (e.g., Cement QCO, Steel QCO, Toys Safety QCO, Helmets QCO, Packaged Drinking Water).

### 6. Negative Relevance Gate
- Implements dual-signal thresholding (Dense Similarity + Lexical BM25).
- Rejects clearly out-of-domain queries (culinary recipes, software coding instructions, nonexistent codes like `IS 99999999`) with **0 hits** rather than returning a hallucinated recommendation. Measured on the probes in `backend/test_wrong_queries.py` and `CPLX-19/20`.
- It is a gate, not a guarantee. Near-domain queries are **not** rejected: an aerospace-materials probe returns results banded MEDIUM with `match_quality: uncertain`, which is the designed behaviour — the confidence band, not the gate, is what tells the officer the match is weak.

---

## 20 Complex Real-World Stress Test Scenarios

Measured by [`backend/test_complex_scenarios.py`](backend/test_complex_scenarios.py); raw output in [`backend/datasets/complex_scenario_results.json`](backend/datasets/complex_scenario_results.json). The exact query text is pinned in the harness so every row below is reproducible.

**Retrieval scenarios: Hit@1 12/18, Hit@3 14/18. Out-of-domain gate: 2/2 rejected.**

| ID | Dimension | Query (as run) | Expected | Top-1 Returned | Hit@1 | Hit@3 |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| **CPLX-01** | Tender Legalese | Municipal PHE tender for centrifugally cast ductile iron pressure pipes | **IS 8329** | IS 1536: 2001 | ❌ | ✅ |
| **CPLX-02** | Tender Legalese | CPWD tender for structural steel sections joists angles and tees | **IS 2062** | IS 2062: 2011 | ✅ | ✅ |
| **CPLX-03** | Tender Legalese | MoRTH highway bridge pre-stressing low relaxation 7-ply strands | **IS 14268** | IS 14268: 1995 | ✅ | ✅ |
| **CPLX-04** | Multi-Part Series | Mild steel wrought pipe fittings Part 2 not tubes Part 1 | **IS 1239 (Part 2)** | IS 432 (Part 1): 1982 | ❌ | ❌ |
| **CPLX-05** | Multi-Part Series | Lithium secondary cells Part 2 not Nickel Part 1 under MeitY CRS | **IS 16046 (Part 2)** | IS 16046 (Part 1): 2018 | ❌ | ✅ |
| **CPLX-06** | Multi-Part Series | Calcined clay Portland pozzolana cement Part 2 not fly ash Part 1 | **IS 1489 (Part 2)** | IS 1489 (Part 2): 1991 | ✅ | ✅ |
| **CPLX-07** | Intent Disambiguation | Method of test for compressive strength of concrete cubes | **IS 516** | IS 516: 1959 | ✅ | ✅ |
| **CPLX-08** | Intent Disambiguation | Method of test for cement fineness by dry sieving 90 micron | **IS 4031 (Part 1)** | IS 4031 (Part 1): 1996 | ✅ | ✅ |
| **CPLX-09** | Intent Disambiguation | Code of practice for design and construction in structural steel | **IS 800** | IS 800: 2007 | ✅ | ✅ |
| **CPLX-10** | Intent Disambiguation | Seismic design criteria and response reduction factor not ductile detailing | **IS 1893** | IS 13920: 2016 | ❌ | ❌ |
| **CPLX-11** | Mandatory QCO | DPIIT mandatory quality control order for children toys safety | **IS 9873** | IS 15644 | ❌ | ❌ |
| **CPLX-12** | Mandatory QCO | MoRTH statutory protective helmets for two-wheeler riders | **IS 4151** | IS 4151: 2015 | ✅ | ✅ |
| **CPLX-13** | Mandatory QCO | Packaged drinking water mandatory ISI mark certification | **IS 14543** | IS 14543: 2016 | ✅ | ✅ |
| **CPLX-14** | MEP Engineering | Three phase outdoor oil-immersed distribution transformers | **IS 1180** | IS 1180: 2018 | ✅ | ✅ |
| **CPLX-15** | MEP Engineering | Code of practice for electrical earthing systems and earth electrodes | **IS 3043** | IS 3043 | ✅ | ✅ |
| **CPLX-16** | MEP Engineering | Submersible pumpsets for deep well irrigation and water supply | **IS 8034** | IS 8034 | ✅ | ✅ |
| **CPLX-17** | Colloquial & Hinglish | RCC chhat ke water leakage ko rokne ke liye waterproofing | **IS 2645** | IS 3370 (Part 2): 2009 | ❌ | ❌ |
| **CPLX-18** | Colloquial & Trade Jargon | Makaan aur building slab dhalai Fe 500D grade sariya TMT bar | **IS 1786** | IS 1786: 2008 | ✅ | ✅ |
| **CPLX-19** | Out-of-Domain Gate | Hyderabadi biryani recipe with basmati rice and saffron | **0 hits** | 0 hits | ✅ | ✅ |
| **CPLX-20** | Out-of-Domain Gate | How do I set up React with Vite and Tailwind CSS | **0 hits** | 0 hits | ✅ | ✅ |

---

## Known Limitations

Every figure below was measured against the shipped `backend/data/standards_master.db`. These are
disclosed rather than fixed because closing them needs data sources we do not have, not more code.

### Scope text is templated, not extracted, for 98.2% of the registry

**32,951 of 33,564 rows (98.2%)** carry a generated sentence as their `scope` field, not text
extracted from the standard itself: `"Indian Standard specification {code} covering requirements,
dimensions, technical properties, sampling, and quality criteria for {title} under {division}."`
(written by `harvest_national_catalog.py:242-256` at ingestion time, from the title and division
alone — never from the standard's actual body text). Only the remaining 613 rows have real,
non-template scope content, carried over from an earlier hand-curated ingestion pass.

This matters beyond the `scope` field on its own: the rationale engine quotes this text as what the
standard "covers," and the CRAG knowledge-strip extractor (Section 3 of `docs/SYSTEM_ANALYSIS.md`)
selects its highlighted sentence from it. For 98.2% of results, both of those are working from a
generated placeholder, not the standard's own scope clause. Closing this requires extracting real
scope text from the standards themselves (licensed full text or a properly parsed source), not a
change to the rationale or knowledge-strip logic, which is working correctly on the input it's given.

### Edition currency

The registry is a **snapshot**, not a live feed. It was harvested from the archive.org `gov.in.is`
mirror and ingested on **2026-09-16** (`MAX(created_at)` in `standards_registry`). That mirror
publishes no supersession feed, so nothing in the pipeline can tell that a harvested edition has
since been replaced.

Spot-checks confirm stale editions are present, and in each case the newer edition is *already in
the registry* but not linked to the older one:

| Harvested row | Status in DB | Newer edition also in DB |
| :--- | :--- | :--- |
| `IS 516: 1959` | ACTIVE, `superseded_by` NULL | `IS 516: 2021` (Hardened Concrete — Methods of Test, Part 1) |
| `IS 694: 1990` | ACTIVE, `superseded_by` NULL | `IS 694: 2010` |
| `IS 12269: 1987` | ACTIVE, `superseded_by` NULL | `IS 12269: 2013` |

Supersession data covers **16 of 33,564 records (0.05%)**, and **11 of those 16 are wrong** — a
prefix-matching bug in the seeder mapped unrelated codes onto `IS 269: 2015`, so
`IS 2692: 1989` (Ferrules for Water Services), `IS 2693: 1989` (Bush Type Flexible Coupling) and
nine `IS 1269x` forestry, shipbuilding and small-tools standards all claim to be superseded by a
cement standard. The 5 correct rows are `IS 269`, `IS 1180 (Part 1)`, `IS 12650`, `IS 9873 (Part 1)`
and `IS 15298 (Part 2)`.

The system therefore **does not claim edition currency**. It shows the snapshot date, labels every
result `In registry` rather than `Current`, marks amendment status as not recorded, and puts edition
verification on the user — in the UI and in clause 4 of every generated GeM specification. Closing
this properly requires a live BIS catalogue feed or a licensed edition register. Until then, verify
at [standardsbis.bsbedge.com](https://standardsbis.bsbedge.com) before citing any code in a tender.

### Allied standards coverage

**2,404 edges across 157 source codes — 0.47% of the 33,564-record registry.** The other 99.5% of
standards return no allied results at all.

The edges are **hand-authored**, not parsed from the normative-reference clauses of the standards
themselves. `is_normative` is derived from a keyword in the target's title, not from how the source
standard actually cites it. Treat the allied tree as a curated starting point for the covered codes,
not as a complete citation graph.

### QCO coverage

**759 products**, scraped from the bis.gov.in Scheme-I listing and crsbis.in. A product that falls
under a Quality Control Order but is not among those 759 will be reported as **voluntary**.

That is a false negative on a legal obligation, and it is the most consequential limitation here: a
procurement officer could read "voluntary" and omit a mandatory ISI mark or CRS registration
requirement from a tender. Always confirm QCO applicability against the current gazette notification.

### Multilingual output

**Input** is genuinely multilingual — BGE-M3 embeds Hindi, Marathi, Tamil, Telugu, Bengali,
Gujarati, Kannada and Hinglish queries directly, and query-side handling is real.

**Output translation is curated for 12 of 33,564 standards** (`CURATED_LOCALIZED_STANDARDS` in
`backend/src/localization/multilingual_engine.py`), across 7 languages. For every other standard the
title is the official English text. Those titles are now explicitly marked as untranslated in the
regional view rather than being wrapped in regional-language framing — e.g. in Hindi:

```
IS 2784 | SHUTTLE FOR AUTOMATIC COP-CHANGING JUTE LOOMS (शीर्षक अनुवाद उपलब्ध नहीं — मूल अंग्रेज़ी)
```

Scope and rationale text for uncurated standards is a regional-language template wrapped around an
English scope excerpt, and is subject to the same limitation.

### Procurement portal integration

The GeM feature **generates clause text** for an officer to copy. It does **not** transact with GeM,
CPPP or GePNIC — there is no API integration, no bid submission, no catalogue lookup and no
authentication against any procurement portal.

---

## Quick Start (Unified Launcher)

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12 (64-bit)
- Windows, Linux, or macOS
- 8 GB RAM (16 GB recommended)

### 2. Setup Virtual Environment
```bash
# Create and activate virtual environment
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# On Linux / macOS:
source .venv/bin/activate

# Install requirements (CPU-optimized PyTorch wheels pre-configured)
pip install -r backend/requirements.txt
```

### 3. Launch System
```bash
python start.py
```
*Or double-click `start.bat` on Windows.*

The unified launcher will:
1. Verify pre-computed vector indexes (`dense_index.faiss`) and SQLite catalog (`standards_master.db`).
2. Start the FastAPI backend at [http://127.0.0.1:8000](http://127.0.0.1:8000).
3. Start the responsive frontend application at [http://localhost:3000](http://localhost:3000).
4. Launch your default browser automatically.

---

## Running Benchmarks & Tests

> The two commands previously documented here pointed at `scratch/comprehensive_complex_test_suite.py`
> and `scratch/run_eval.py`. No `scratch/` directory exists in this repository and neither script is in
> its git history, so those commands could never have run. They are replaced below with scripts that do.

### Run the 20 complex stress-test scenarios
```bash
cd backend && python test_complex_scenarios.py
```
Writes `backend/datasets/complex_scenario_results.json`. Current result: Hit@1 12/18, Hit@3 14/18 on
the retrieval scenarios, 2/2 on the out-of-domain probes.

### Run the out-of-domain guard probes
```bash
cd backend && python test_wrong_queries.py
```

### Run the official benchmarks (National + Public test sets)
```bash
cd backend && python inference.py -i datasets/national_evaluation_test_set.json -o datasets/national_test_results.json
cd backend && python eval_script.py --results datasets/national_test_results.json
```

---

## API Reference

Interactive API documentation is available out-of-the-box:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/search` | `POST` | Hybrid BM25 + FAISS + Cross-Encoder retrieval with CRAG strips & rationales |
| `/tender-audit` | `POST` | Multipart PDF/CSV tender document parser and clause auditor |
| `/gem-clause` | `POST` | Generates compliant GeM technical specification text |
| `/standards/{is_code}` | `GET` | Retrieves full standard metadata, QCO rules, and knowledge graph relations |
| `/health` | `GET` | System health, model readiness, and index diagnostics |

---

## Detailed Backend Documentation

For deep technical architectural specifications, database schemas, and mathematical formulations:

👉 **[Read the Backend Technical Guide (`backend/README.md`)](backend/README.md)**

