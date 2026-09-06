# Indian Standards (BIS) Recommendation Engine

> **AI-Powered Recommendation & Compliance Engine for Bureau of Indian Standards (BIS)**  
> Engineered for real-time tender specification auditing, mandatory Quality Control Order (QCO) enforcement, and Government e-Marketplace (GeM) procurement clause generation.

---

## Highlights

- **Hybrid Semantic Retrieval**: Blends BM25 lexical search with BGE-M3 (1024-d dense vector embeddings via FAISS) using Reciprocal Rank Fusion (RRF).
- **Hardware-Adaptive Cross-Encoder Reranking**: Utilizes `bge-reranker-v2-m3` with an automatic hardware ladder that clamps candidate pool on CPU systems (e.g. Intel i3/i5) to guarantee $<2\text{s}$ per-query latency targets.
- **Strict IS-Code Whitelist Guard**: Eliminates hallucinations by constraining results strictly to authentic BIS standards.
- **Regulatory QCO Compliance**: Automatically checks candidate standards against mandatory Quality Control Orders under the BIS Act, 2016.
- **Tender Document Parser**: Audits technical specification clauses and Bill of Quantities (BoQ) from uploaded PDFs and CSV files.
- **100% Offline Capable**: Fully functional on local machines without mandatory internet or paid cloud API dependencies.

---

## Quick Start (Unified Launcher)

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12 (64-bit)
- Windows, Linux, or macOS

### 2. Setup Virtual Environment
```bash
# Create and activate virtual environment
python -m venv .venv

# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# On Linux / macOS:
source .venv/bin/activate

# Install requirements
pip install -r backend/requirements.txt
```

### 3. Launch System
```bash
python start.py
```
*Or double-click `start.bat` on Windows.*

The launcher will:
1. Verify pre-computed indexes (`dense_index.faiss` and `bm25_index.pkl`).
2. Start the FastAPI backend at [http://127.0.0.1:8000](http://127.0.0.1:8000).
3. Start the test frontend at [http://localhost:3000](http://localhost:3000).
4. Open your browser automatically.

---

## Detailed Documentation

For comprehensive backend architecture, installation details, API documentation, and evaluation benchmarks, refer to:

👉 **[Backend Documentation (`backend/README.md`)](file:///c:/Users/Amit/OneDrive/Desktop/programing/Git/IS-Recommedation-Engine/backend/README.md)**
