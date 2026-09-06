# Indian Standards (BIS) Recommendation Engine — Backend

A production-grade, offline-first AI recommendation engine engineered for the Bureau of Indian Standards (BIS). It automatically retrieves, validates, and recommends relevant Indian Standards (IS), identifies mandatory Quality Control Orders (QCO), detects superseded standards, audits tender documents (PDF/CSV), and generates procurement clauses for the Government e-Marketplace (GeM).

---

## Architecture Overview

```
User Query / Tender Document (PDF/CSV)
                  │
                  ▼
       ┌─────────────────────┐
       │ Ingestion & Parsing │
       └──────────┬──────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌───────────────┐   ┌────────────────┐
│  BM25 Lexical │   │  BGE-M3 Dense  │
│  Search (K=25)│   │  FAISS (K=25)  │
└───────┬───────┘   └───────┬────────┘
        │                   │
        └─────────┬─────────┘
                  ▼
      ┌─────────────────────────┐
      │ Reciprocal Rank Fusion  │
      │       (RRF C=60)        │
      └───────────┬─────────────┘
                  ▼
      ┌─────────────────────────┐
      │ Hardware Auto-Clamp     │  ◄── Dynamically scales candidate pool (3 on CPU,
      │ bge-reranker-v2-m3      │      up to 25 on GPU) to preserve <2s latency target
      └───────────┬─────────────┘
                  ▼
      ┌─────────────────────────┐
      │ IS-Code Whitelist Guard │  ◄── Eliminates hallucinations
      └───────────┬─────────────┘
                  ▼
      ┌─────────────────────────┐
      │  SQLite Standards DB    │  ◄── Enriches with QCO mandates, active/superseded
      │   & Knowledge Graph     │      status, and allied standards
      └───────────┬─────────────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
┌───────────────┐   ┌────────────────┐
│  GeM Clause   │   │ Grounded Rationale
│   Generator   │   │  Engine        │
└───────────────┘   └────────────────┘
```

### Key Technical Pillars
1. **Hybrid Retrieval**: Fuses BM25 keyword matching (for exact IS designations, material grades, and alphanumeric codes) with FAISS dense vector search (BGE-M3 1024-d embeddings for rich semantic matching).
2. **Dynamic Hardware Auto-Clamp Reranker**: On CPU-only systems (e.g., Intel i3/i5), the rerank candidate pool automatically clamps to 3 pairs to keep query latency under 2 seconds without degrading Hit@3. On CUDA systems, it unlocks up to full capacity.
3. **Strict Whitelist Guard & QCO Compliance**: Prevents hallucinated standard codes and checks every candidate against mandatory Quality Control Orders issued under the BIS Act, 2016.
4. **100% Offline Capable**: All embedding, reranking, parsing, and rationale components function fully offline without external API dependencies.

---

## Directory Structure

```
backend/
├── build_indices.py            # Builds SQLite DB, BM25 index, and FAISS vector index
├── download_models.py          # Pre-downloads BGE-M3 and BGE-Reranker (filtered formats)
├── eval_script.py              # Computes Hit@3, MRR@5, and latency metrics
├── inference.py                # Standalone CLI evaluation script
├── requirements.txt            # Python dependencies (CPU-optimized PyTorch)
├── team_results.json           # Benchmark evaluation dataset
├── data/
│   ├── index/
│   │   ├── bm25_index.pkl      # Pickled BM25 lexical index
│   │   ├── dense_index.faiss   # 1024-dimensional FAISS index
│   │   └── dense_metadata.json # Mapping of FAISS vector IDs to standard records
│   ├── is_code_whitelist.json  # Validated catalog of authentic IS codes
│   ├── parsed_standards.json   # Full standard records (title, scope, year, status)
│   ├── qco_mandatory_catalog.json # Mandatory QCO orders & gazette references
│   ├── raw_xrefs.json          # Allied standard citation graph
│   └── standards_master.db     # SQLite database for relational & graph lookups
└── src/
    ├── api/
    │   └── fastapi_application.py # FastAPI REST endpoints
    ├── compliance/
    │   └── qco_mandatory_engine.py# QCO legal mandate checker
    ├── database/
    │   └── sqlite_manager.py      # SQLite schema, queries, and seeding logic
    ├── graph/
    │   └── allied_standards_classifier.py # Knowledge graph edge traversal
    ├── ingestion/
    │   └── tender_document_parser.py # PDF (PyMuPDF) and CSV BoQ parser
    ├── llm/
    │   └── grounded_rationale_engine.py # Offline justification generator
    ├── procurement/
    │   └── gem_specification_generator.py # GeM technical specification builder
    └── retrieval/
        ├── bge_multilingual_embedder.py   # BAAI/bge-m3 vector embedder
        ├── bm25_lexical_indexer.py        # BM25 indexing and query engine
        ├── cross_encoder_reranker.py      # BAAI/bge-reranker-v2-m3 with auto-clamp
        ├── faiss_vector_indexer.py        # FAISS index wrapper
        └── hybrid_search_orchestrator.py  # End-to-end RRF + Rerank pipeline
```

---

## System Requirements

| Requirement | Minimum | Recommended |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11, Ubuntu 20.04+, macOS | Windows 11 / Linux x86_64 |
| **Python** | Python 3.10, 3.11, or 3.12 (64-bit) | Python 3.11 or 3.12 |
| **RAM** | 8 GB | 16 GB |
| **Disk Space** | 4 GB free space | 8 GB free space |
| **Compute** | Multi-core CPU (Intel i3/i5/i7, AMD Ryzen) | NVIDIA GPU with 4GB+ VRAM (Optional) |

---

## Installation & Setup

### Step 1: Clone or Navigate to the Repository
Open your terminal (PowerShell, Command Prompt, or Bash):
```bash
cd /path/to/IS-Recommedation-Engine
```

### Step 2: Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell blocks script execution, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

**On Windows (Command Prompt):**
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 3: Upgrade Pip and Install Dependencies

Install all core dependencies:
```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

> [!NOTE]
> The `requirements.txt` file is pre-configured with `--extra-index-url https://download.pytorch.org/whl/cpu` to install lightweight, CPU-optimized PyTorch binaries (~180MB instead of ~2.5GB CUDA packages). If you have an NVIDIA GPU and wish to use CUDA, install PyTorch with CUDA support first:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cu121
> pip install -r backend/requirements.txt
> ```

---

### Step 4: Download AI Models

The engine uses two pre-trained models from Hugging Face:
- `BAAI/bge-m3` (Dense Embedding, ~2.2 GB)
- `BAAI/bge-reranker-v2-m3` (Cross-Attention Reranker, ~1.1 GB)

Run the automated pre-downloader script:
```bash
python backend/download_models.py
```
*This script automatically filters out redundant ONNX, OpenVINO, Flax, and TensorFlow files, saving over 8 GB of unnecessary downloads.*

---

### Step 5: Seed Database & Build Indexes (If Not Already Built)

Pre-computed index files are bundled in `backend/data/index/`. If you need to rebuild them from raw JSON sources:
```bash
python backend/build_indices.py
```
This script:
1. Seeds the SQLite database `backend/data/standards_master.db`.
2. Builds the BM25 lexical index `backend/data/index/bm25_index.pkl`.
3. Encodes all standard scopes into `backend/data/index/dense_index.faiss`.

---

## Running the Backend

### Option A: Using the Unified Application Launcher (Recommended)
From the repository root:
```bash
python start.py
```
Or on Windows:
```cmd
start.bat
```
This automatically verifies indexes, starts the FastAPI backend on `http://127.0.0.1:8000`, launches the test frontend on `http://localhost:3000`, and opens your browser.

### Option B: Running FastAPI Directly with Uvicorn
From the `backend/` directory:
```bash
cd backend
uvicorn src.api.fastapi_application:app --host 127.0.0.1 --port 8000 --reload
```

Once started, explore the interactive documentation:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## REST API Endpoints

### 1. Hybrid Search (`POST /search`)
Performs hybrid BM25 + FAISS search, cross-encoder reranking, QCO rule matching, and rationale generation.

**Request Payload:**
```json
{
  "query": "Ordinary Portland Cement 43 grade construction",
  "top_k": 3,
  "use_cloud_llm": false
}
```

**Response:**
```json
{
  "query": "Ordinary Portland Cement 43 grade construction",
  "hits": [
    {
      "rank": 1,
      "is_code": "IS 8112",
      "title": "Ordinary Portland Cement, 43 Grade — Specification",
      "scope": "Covers manufacture and chemical/physical requirements of 43 grade OPC...",
      "rerank_score": 0.942,
      "rrf_score": 0.0328,
      "confidence": "HIGH",
      "status": "ACTIVE",
      "superseded_by": null,
      "qco_rules": [
        {
          "order_name": "Cement (Quality Control) Order, 2003",
          "mandate": "MANDATORY",
          "notified_date": "2003-02-17"
        }
      ],
      "allied_standards": [
        { "is_code": "IS 4031", "relationship": "TESTING_METHOD" }
      ],
      "rationale": "Direct match for 43-grade Ordinary Portland Cement specifications. Subject to mandatory QCO certification."
    }
  ],
  "latency_seconds": 1.42
}
```

---

### 2. Tender Document Audit (`POST /tender-audit`)
Accepts multipart file upload (`.pdf` or `.csv`) representing tender technical specifications or Bill of Quantities (BoQ), extracts technical clauses or line items, and audits them against the BIS database.

**Form Data:**
- `file`: Tender PDF or CSV file.

**Response (PDF Sample):**
```json
{
  "type": "pdf_spec",
  "total_pages": 12,
  "has_scanned_pages": false,
  "clauses_analyzed": [
    {
      "clause_text": "Supply of structural steel sections conforming to IS specifications...",
      "recommended_standards": [
        { "is_code": "IS 2062", "title": "Hot Rolled Medium and High Tensile Structural Steel", "confidence": "HIGH", "status": "ACTIVE" }
      ]
    }
  ],
  "warning": null
}
```

---

### 3. GeM Specification Clause Generator (`POST /gem-clause`)
Produces pre-formatted, legally binding technical specification text formatted for Government e-Marketplace (GeM) tender creation.

**Request Payload:**
```json
{
  "is_code": "IS 456"
}
```

**Response:**
```json
{
  "is_code": "IS 456",
  "clause_text": "The offered product/workmanship shall strictly comply with Indian Standard IS 456 (Plain and Reinforced Concrete - Code of Practice)...",
  "mandatory_qco": false,
  "status": "ACTIVE"
}
```

---

### 4. Single Standard Details (`GET /standards/{is_code}`)
Retrieves full metadata, QCO rules, and allied graph relations for a specific Indian Standard.

**Example Request:**
```bash
curl -X GET "http://127.0.0.1:8000/standards/IS%208112"
```

---

### 5. Benchmark Evaluation (`POST /judge_search`)
High-throughput evaluation endpoint tailored for automated judge evaluation scripts and benchmark validation.

---

## Environment Variables & Configuration

Configuration flags can be set in an optional `.env` file in the root or backend directory:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `HF_HUB_DISABLE_XET` | `1` | Disables XET protocol to avoid symlink hanging on Windows systems. |
| `RERANK_K` | Auto | Overrides dynamic hardware ladder and forces an exact rerank pool size (e.g., `RERANK_K=5`). |
| `RERANK_K_NO_AUTO` | `0` | Disables auto-clamping ladder and uses `requested_k` directly. |
| `GEMINI_API_KEY` | *(Optional)* | Enables optional Google Gemini Cloud LLM rationale enrichment. |

---

## Benchmarking & Evaluation

To evaluate accuracy against the benchmark evaluation set:
```bash
python backend/eval_script.py backend/team_results.json
```

**Target Benchmarks:**
- **Hit Rate @3**: $\ge 80\%$
- **Mean Reciprocal Rank (MRR @5)**: $\ge 0.70$
- **Average Latency**: $< 2.0\text{s}$ per query on CPU

---

## Troubleshooting

### 1. `torch` or `sentence-transformers` Import Errors
Ensure your virtual environment is active. Reinstall the CPU wheels:
```bash
pip install --force-reinstall --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
```

### 2. Hugging Face Download Hanging on Windows
Windows symlinks can cause downloads to stall if Developer Mode is disabled. Ensure `HF_HUB_DISABLE_XET=1` is set (already included in `download_models.py` and `cross_encoder_reranker.py`).

### 3. Port 8000 Already in Use
If another service is using port 8000, specify a different port:
```bash
uvicorn src.api.fastapi_application:app --host 127.0.0.1 --port 8001
```
