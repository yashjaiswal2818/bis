"""FastAPI Application for Indian Standards Recommendation Engine.

Exposes endpoints for semantic search, judge sandbox scoring, tender PDF/CSV audit,
allied standards graph inspection, and GeM specification clause generation.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.compliance.tender_compliance_auditor import TenderComplianceAuditor
from src.database.sqlite_manager import get_standard_details
from src.ingestion.tender_document_parser import TenderDocumentParser
from src.llm.grounded_rationale_engine import GroundedRationaleEngine
from src.localization.multilingual_engine import get_multilingual_representations
from src.procurement.gem_specification_generator import GeMSpecificationGenerator
from src.retrieval.hybrid_search_orchestrator import HybridSearchOrchestrator

# Global State Container
STATE: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes models and managers into memory on startup."""
    print("[API] Initializing Hybrid Search Orchestrator...")
    t0 = time.perf_counter()
    STATE["orchestrator"] = HybridSearchOrchestrator()
    STATE["gem_generator"] = GeMSpecificationGenerator()
    STATE["rationale_engine"] = GroundedRationaleEngine()
    STATE["compliance_auditor"] = TenderComplianceAuditor()
    print(f"[API] Ready in {time.perf_counter() - t0:.2f}s")
    yield


app = FastAPI(
    title="Indian Standards (BIS) Recommendation Engine",
    description="AI-powered recommendation engine for Indian Standards, QCO compliance, and procurement tenders.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Schemas ---

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Product description, technical specification, or standard number")
    top_k: int = Field(5, ge=1, le=20, description="Number of standards to recommend")
    use_cloud_llm: bool = Field(False, description="Enable cloud LLM generation if internet key available")


class StandardHit(BaseModel):
    rank: int
    is_code: str
    title: str
    scope: str
    rerank_score: float
    rrf_score: float
    confidence: str
    status: str
    superseded_by: str | None = None
    qco_rules: list[dict[str, Any]] = Field(default_factory=list)
    allied_standards: list[dict[str, Any]] = Field(default_factory=list)
    reaffirmation_year: int | None = None
    amendments_count: int = 0
    rationale: str
    is_government_schedule_match: bool = False
    schedule_item_title: str | None = None
    schedule_category: str | None = None
    matched_grade: str | None = None
    translations: dict[str, dict[str, str]] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    hits: list[StandardHit]
    latency_seconds: float


class GeMClauseRequest(BaseModel):
    is_code: str


# --- Endpoints ---

@app.get("/health")
def health_check():
    """Health check endpoint confirming engine readiness."""
    return {
        "status": "healthy",
        "offline_ready": True,
        "models_loaded": "orchestrator" in STATE,
    }


@app.post("/search", response_model=SearchResponse)
def search_standards(req: SearchRequest):
    """Performs full hybrid semantic search, QCO lookup, and rationale generation."""
    orchestrator: HybridSearchOrchestrator = STATE.get("orchestrator")
    rationale_engine: GroundedRationaleEngine = STATE.get("rationale_engine")
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Search engine initializing")

    t0 = time.perf_counter()
    recs = orchestrator.search(req.query, top_k=req.top_k)
    latency = time.perf_counter() - t0

    hits = []
    for r in recs:
        rat = rationale_engine.generate_rationale(
            query=req.query,
            is_code=r.is_code,
            title=r.title,
            scope=r.scope,
            qco_rules=r.qco_rules,
            confidence=r.confidence,
            use_cloud_llm=req.use_cloud_llm,
        )
        trans = get_multilingual_representations(
            is_code=r.is_code,
            title=r.title,
            scope=r.scope,
            qco_rules=r.qco_rules,
            confidence=r.confidence,
        )
        hits.append(StandardHit(
            rank=r.rank,
            is_code=r.is_code,
            title=r.title,
            scope=r.scope,
            rerank_score=r.rerank_score,
            rrf_score=r.rrf_score,
            confidence=r.confidence,
            status=r.status,
            superseded_by=r.superseded_by,
            qco_rules=r.qco_rules,
            allied_standards=r.allied_standards,
            reaffirmation_year=r.reaffirmation_year,
            amendments_count=r.amendments_count,
            rationale=rat,
            is_government_schedule_match=r.is_government_schedule_match,
            schedule_item_title=r.schedule_item_title,
            schedule_category=r.schedule_category,
            matched_grade=r.matched_grade,
            translations=trans,
        ))

    return SearchResponse(query=req.query, hits=hits, latency_seconds=round(latency, 3))


@app.post("/judge_search")
def judge_search(req: SearchRequest):
    """Raw judge evaluation endpoint mirroring inference.py for benchmark scoring."""
    orchestrator: HybridSearchOrchestrator = STATE.get("orchestrator")
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Engine initializing")

    t0 = time.perf_counter()
    recs = orchestrator.search(req.query, top_k=req.top_k)
    latency = time.perf_counter() - t0

    return {
        "query": req.query,
        "retrieved_standards": [r.is_code for r in recs],
        "latency_seconds": round(latency, 3),
    }


@app.post("/tender-audit")
async def audit_tender_document(file: UploadFile = File(...)):
    """Uploads and audits a tender document (PDF or CSV BoQ) for applicable Indian Standards and Hallmarking/ISI compliance."""
    orchestrator: HybridSearchOrchestrator = STATE.get("orchestrator")
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Engine initializing")
    auditor: TenderComplianceAuditor = STATE.get("compliance_auditor")
    if not auditor:
        auditor = TenderComplianceAuditor()

    contents = await file.read()
    filename = file.filename or "tender.pdf"

    if filename.endswith(".csv"):
        text = contents.decode("utf-8", errors="ignore")
        extraction = TenderDocumentParser.parse_csv_boq(text, filename=filename)
        results = []
        for item in extraction.boq_items[:10]:
            desc = item["description"]
            recs = orchestrator.search(desc, top_k=3)
            verdict = auditor.audit_clause(desc, recs)
            results.append({
                "item_description": desc,
                "quantity": item.get("quantity"),
                "unit": item.get("unit"),
                "compliance_verdict": verdict.to_dict(),
                "recommended_standards": [
                    {"is_code": r.is_code, "title": r.title, "confidence": r.confidence, "status": r.status}
                    for r in recs
                ],
            })
        summary = auditor.summarize_document_audit([r["compliance_verdict"] for r in results])
        return {
            "type": "boq",
            "items_audited": results,
            "warning": extraction.warning_message,
            **summary,
        }
    else:
        # PDF Parsing
        extraction = TenderDocumentParser.parse_pdf_bytes(contents, filename=filename)
        results = []

        # Audit structured BoQ items if extracted from PDF tables
        for item in extraction.boq_items[:10]:
            desc = item["description"]
            recs = orchestrator.search(desc[:300], top_k=3)
            verdict = auditor.audit_clause(desc, recs)
            results.append({
                "clause_text": desc[:200] + ("..." if len(desc) > 200 else ""),
                "item_description": desc,
                "quantity": item.get("quantity"),
                "unit": item.get("unit"),
                "compliance_verdict": verdict.to_dict(),
                "recommended_standards": [
                    {"is_code": r.is_code, "title": r.title, "confidence": r.confidence, "status": r.status}
                    for r in recs
                ],
            })

        # Audit technical clauses / decomposed items
        for clause in extraction.technical_clauses[:10]:
            if any(clause.lower() in (r.get("clause_text") or "").lower() for r in results):
                continue
            recs = orchestrator.search(clause[:300], top_k=3)
            verdict = auditor.audit_clause(clause, recs)
            results.append({
                "clause_text": clause[:200] + ("..." if len(clause) > 200 else ""),
                "compliance_verdict": verdict.to_dict(),
                "recommended_standards": [
                    {"is_code": r.is_code, "title": r.title, "confidence": r.confidence, "status": r.status}
                    for r in recs
                ],
            })
        summary = auditor.summarize_document_audit([r["compliance_verdict"] for r in results])
        return {
            "type": "pdf_spec",
            "total_pages": extraction.total_pages_or_rows,
            "has_scanned_pages": extraction.has_scanned_pages,
            "clauses_analyzed": results,
            "warning": extraction.warning_message,
            **summary,
        }


@app.post("/gem-clause")
def generate_gem_clause(req: GeMClauseRequest):
    """Generates an official GeM-ready technical specification clause for a standard."""
    gem_generator: GeMSpecificationGenerator = STATE.get("gem_generator")
    clause = gem_generator.generate_clause(req.is_code)
    return clause


@app.get("/standards/{is_code}")
def get_standard(is_code: str):
    """Retrieves standard details, QCO compliance rules, and allied graph relations."""
    details = get_standard_details(is_code)
    if not details:
        raise HTTPException(status_code=404, detail="Standard not found")
    return details
