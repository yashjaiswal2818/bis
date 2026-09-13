# Indian Standards (BIS) Recommendation Engine

> **100% Offline, Zero-Hallucination AI Recommendation & Regulatory Compliance Engine for the Bureau of Indian Standards (BIS)**  
> Engineered for real-time tender specification auditing, mandatory Quality Control Order (QCO) enforcement, automated Government e-Marketplace (GeM) procurement clause generation, and cross-encoder precision search.

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![Hit@1 Accuracy](https://img.shields.io/badge/Hit%401-100.0%25-brightgreen)](backend/datasets/national_test_results.json)
[![MRR@5](https://img.shields.io/badge/MRR%405-1.0000-brightgreen)](backend/datasets/national_test_results.json)
[![Complex Queries Stress Test](https://img.shields.io/badge/Complex%20Queries-20%2F20%20(100%25)-success)](backend/datasets/national_test_results.json)
[![Offline Capable](https://img.shields.io/badge/Offline%20First-100%25-orange)]()

---

## Benchmark Performance Highlights

Our **Domain-Adapted Local Corrective RAG (CRAG)** architecture achieves a **perfect 100% Hit@1 and 1.0000 MRR@5** across official benchmark evaluations and rigorous real-world stress testing:

| Benchmark / Evaluation Suite | Queries Tested | Hit Rate @ 1 | Hit Rate @ 3 | MRR @ 5 | Accuracy |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Official National Benchmark** (`national_evaluation_test_set.json`) | 15 | **100.0% (15/15)** | **100.0% (15/15)** | **1.0000** | **100%** |
| **Public Evaluation Test Set** (`public_test_set.json`) | 10 | **100.0% (10/10)** | **100.0% (10/10)** | **1.0000** | **100%** |
| **Comprehensive Complex Queries Matrix** (7 Dimensions) | 20 | **100.0% (18/18)** | **100.0% (18/18)** | **1.0000** | **100% (20/20)** |
| **Zero-Hallucination Out-of-Domain Guard** | 2 | — | — | — | **100% (2/2 Rejected)** |

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
       │   Auto-clamps candidate pool on CPU (<2.5s latency)    │
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
- Seamlessly handles regional Indian languages (**Hindi, Marathi, Tamil, Telugu**) and conversational Hinglish (`"RCC chhat ke water leakage ko rokne ke liye waterproofing compound"`, `"Makaan aur building slab dhalai Fe 500D grade sariya"`).
- Normalizes Devanagari numerals (`०-९`) to standard Arabic digits.

### 5. Mandatory Quality Control Order (QCO) Enforcement
- Cross-references candidate standards with gazetted Quality Control Orders issued under the BIS Act, 2016.
- Flags legally mandatory standards (e.g., Cement QCO, Steel QCO, Toys Safety QCO, Helmets QCO, Packaged Drinking Water).

### 6. Zero-Hallucination Negative Relevance Gate
- Implements strict dual-signal thresholding (Dense Similarity + Lexical BM25).
- Completely rejects out-of-domain queries (e.g., culinary recipes, software coding instructions, nonexistent codes like `IS 99999999`) returning **0 hits** to avoid hallucinated recommendations.

---

## 20 Complex Real-World Stress Test Scenarios

Tested across 7 diverse engineering dimensions:

| ID | Dimension | Query Scenario | Expected Code | Status |
| :--- | :--- | :--- | :---: | :---: |
| **CPLX-01** | Tender Legalese | Municipal PHE tender for centrifugally cast DI pressure pipes | **IS 8329** | ✅ PASS |
| **CPLX-02** | Tender Legalese | CPWD tender for structural steel sections (joists, angles, tees) | **IS 2062** | ✅ PASS |
| **CPLX-03** | Tender Legalese | MoRTH Highway bridge pre-stressing low relaxation 7-ply strands | **IS 14268** | ✅ PASS |
| **CPLX-04** | Multi-Part Series | Mild steel wrought pipe fittings (Part 2) vs tubes (Part 1) | **IS 1239 (Part 2)** | ✅ PASS |
| **CPLX-05** | Multi-Part Series | Lithium secondary cells (Part 2) vs Nickel (Part 1) under MeitY CRS | **IS 16046 (Part 2)** | ✅ PASS |
| **CPLX-06** | Multi-Part Series | Calcined clay PPC (Part 2) vs Fly ash PPC (Part 1) | **IS 1489 (Part 2)** | ✅ PASS |
| **CPLX-07** | Intent Disambiguation | Method of test for compressive strength of concrete cubes | **IS 516** | ✅ PASS |
| **CPLX-08** | Intent Disambiguation | Method of test for cement fineness by dry sieving (90 micron) | **IS 4031 (Part 1)** | ✅ PASS |
| **CPLX-09** | Intent Disambiguation | Code of practice for design and construction in structural steel | **IS 800** | ✅ PASS |
| **CPLX-10** | Intent Disambiguation | Seismic design criteria & response reduction vs ductile detailing | **IS 1893** | ✅ PASS |
| **CPLX-11** | Mandatory QCO | DPIIT Mandatory Quality Control Order for children toys safety | **IS 9873** | ✅ PASS |
| **CPLX-12** | Mandatory QCO | MoRTH statutory protective helmets for two-wheeler riders | **IS 4151** | ✅ PASS |
| **CPLX-13** | Mandatory QCO | Packaged drinking water mandatory ISI mark certification | **IS 14543** | ✅ PASS |
| **CPLX-14** | MEP Engineering | Three phase outdoor oil-immersed distribution transformers | **IS 1180** | ✅ PASS |
| **CPLX-15** | MEP Engineering | Code of practice for electrical earthing systems and earth electrodes | **IS 3043** | ✅ PASS |
| **CPLX-16** | MEP Engineering | Submersible pumpsets for deep well irrigation and water supply | **IS 8034** | ✅ PASS |
| **CPLX-17** | Colloquial & Hinglish | *"RCC chhat ke water leakage ko rokne ke liye waterproofing"* | **IS 2645** | ✅ PASS |
| **CPLX-18** | Colloquial & Trade Jargon | *"Makaan aur building slab dhalai Fe 500D grade sariya TMT bar"* | **IS 1786** | ✅ PASS |
| **CPLX-19** | Zero-Hallucination Gate | Culinary recipe (Hyderabadi biryani) — Out-of-domain | **NONE (0 hits)** | ✅ PASS |
| **CPLX-20** | Zero-Hallucination Gate | Web programming question (React Vite Tailwind) — Out-of-domain | **NONE (0 hits)** | ✅ PASS |

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

### Run Comprehensive Complex Stress-Tests (20 Queries)
```powershell
backend\venv\Scripts\python.exe -u scratch/comprehensive_complex_test_suite.py
```

### Run Official Hackathon Benchmarks (National + Public Test Sets)
```powershell
backend\venv\Scripts\python.exe -u scratch/run_eval.py
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

👉 **[Read the Backend Technical Guide (`backend/README.md`)](file:///c:/Users/Amit/OneDrive/Desktop/programing/Git/IS-Recommedation-Engine/backend/README.md)**

