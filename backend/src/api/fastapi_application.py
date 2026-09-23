"""FastAPI Application for Indian Standards Recommendation Engine.

Exposes endpoints for semantic search, judge sandbox scoring, tender PDF/CSV audit,
allied standards graph inspection, and GeM specification clause generation.
"""
from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.compliance.tender_compliance_auditor import TenderComplianceAuditor
from src.database.sqlite_manager import get_connection, get_standard_details
from src.ingestion.tender_document_parser import TenderDocumentParser, technical_relevance_score
from src.llm.grounded_rationale_engine import GroundedRationaleEngine
from src.integration.apisetu_gateway import APISetuBISGateway
from src.localization.multilingual_engine import get_multilingual_representations
from src.procurement.gem_specification_generator import GeMSpecificationGenerator
from src.retrieval.hybrid_search_orchestrator import HybridSearchOrchestrator
from src.compliance.edition_resolver import EditionResolver

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
    STATE["apisetu_gateway"] = APISetuBISGateway()
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
    edition_context: dict | None = None
    schedule_item_title: str | None = None
    schedule_category: str | None = None
    matched_grade: str | None = None
    knowledge_strip: str | None = None
    translations: dict[str, dict[str, str]] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    hits: list[StandardHit]
    latency_seconds: float
    match_quality: str = "confident"  # 'confident' | 'uncertain' | 'no_match'


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
            knowledge_strip=r.knowledge_strip,
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
            edition_context=r.edition_context,
            schedule_item_title=r.schedule_item_title,
            schedule_category=r.schedule_category,
            matched_grade=r.matched_grade,
            knowledge_strip=r.knowledge_strip,
            translations=trans,
        ))

    # Derived from the single confidence decision point (get_confidence_band) on the top hit
    if not hits:
        match_quality = "no_match"
    elif hits[0].confidence == "HIGH":
        match_quality = "confident"
    else:
        match_quality = "uncertain"

    return SearchResponse(
        query=req.query,
        hits=hits,
        latency_seconds=round(latency, 3),
        match_quality=match_quality,
    )


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


# Each audited line item runs a full hybrid search (measured ~6-10 s on CPU), so the cap is a
# latency guard, not a parser limit. The response always reports items_parsed vs items_assessed
# so the UI can say how many rows were left out. Override with TENDER_AUDIT_MAX_ITEMS.
MAX_AUDIT_ITEMS = int(os.getenv("TENDER_AUDIT_MAX_ITEMS", "10"))

# A clause that scores below zero matched an explicit administrative/eligibility keyword
# (EMD, turnover, pre-qualification, arbitration, ...) -- see technical_relevance_score.
# Running full retrieval against it anyway is how administrative and eligibility text
# ended up with plausible-looking "Recommended Standards" next to it (e.g. JV
# pre-qualification bullets matched against unrelated IS codes purely on stray word
# overlap). Below this floor we skip retrieval entirely and say so honestly instead.
TECHNICAL_RELEVANCE_FLOOR = 0
_SKIP_REASON = (
    "Reads as administrative or eligibility text, not a technical or product "
    "specification -- not searched against the standards index."
)


def _search_if_technical(
    orchestrator: HybridSearchOrchestrator, text: str, top_k: int = 3
) -> tuple[list[Any], str | None]:
    """Runs retrieval only if `text` clears the technical-relevance floor. Returns
    (recs, skip_reason) -- skip_reason is set (and recs is []) when retrieval was never
    run, so the caller can report an honest "not searched" reason via
    TenderComplianceAuditor.audit_clause(..., skip_reason=...) instead of a genuine
    empty-search result being confused with administrative text that was never searched."""
    if technical_relevance_score(text) < TECHNICAL_RELEVANCE_FLOOR:
        return [], _SKIP_REASON
    return orchestrator.search(text[:300], top_k=top_k), None


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
        items_parsed = len(extraction.boq_items)
        for item in extraction.boq_items[:MAX_AUDIT_ITEMS]:
            desc = item["description"]
            recs, skip_reason = _search_if_technical(orchestrator, desc)
            verdict = auditor.audit_clause(desc, recs, skip_reason=skip_reason)
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
        summary = auditor.summarize_document_audit(
            [r["compliance_verdict"] for r in results], items_parsed=items_parsed
        )
        return {
            "type": "boq",
            "items_audited": results,
            "warning": extraction.warning_message,
            "audit_cap": MAX_AUDIT_ITEMS,
            "audit_truncated": items_parsed > len(results),
            **summary,
        }
    else:
        # PDF Parsing
        extraction = TenderDocumentParser.parse_pdf_bytes(contents, filename=filename)
        results = []

        # Audit structured BoQ items if extracted from PDF tables
        items_parsed = len(extraction.boq_items) + len(extraction.technical_clauses)
        for item in extraction.boq_items[:MAX_AUDIT_ITEMS]:
            desc = item["description"]
            recs, skip_reason = _search_if_technical(orchestrator, desc)
            verdict = auditor.audit_clause(desc, recs, skip_reason=skip_reason)
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

        # Audit technical clauses / decomposed items, up to the same overall cap
        for clause in extraction.technical_clauses:
            if len(results) >= MAX_AUDIT_ITEMS:
                break
            if any(clause.lower() in (r.get("clause_text") or "").lower() for r in results):
                continue
            recs, skip_reason = _search_if_technical(orchestrator, clause)
            verdict = auditor.audit_clause(clause, recs, skip_reason=skip_reason)
            results.append({
                "clause_text": clause[:200] + ("..." if len(clause) > 200 else ""),
                "compliance_verdict": verdict.to_dict(),
                "recommended_standards": [
                    {"is_code": r.is_code, "title": r.title, "confidence": r.confidence, "status": r.status}
                    for r in recs
                ],
            })
        summary = auditor.summarize_document_audit(
            [r["compliance_verdict"] for r in results], items_parsed=items_parsed
        )
        return {
            "type": "pdf_spec",
            "total_pages": extraction.total_pages_or_rows,
            "has_scanned_pages": extraction.has_scanned_pages,
            "clauses_analyzed": results,
            "warning": extraction.warning_message,
            "audit_cap": MAX_AUDIT_ITEMS,
            "audit_truncated": items_parsed > len(results),
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


# --- NeGD API Setu Compliant Endpoints ---

@app.get("/api/v1/bis/standards/{is_code}")
def apisetu_get_standard(is_code: str):
    """NeGD API Setu endpoint: standard metadata, currency, and mandatory certification."""
    gateway: APISetuBISGateway = STATE.get("apisetu_gateway")
    if not gateway:
        gateway = APISetuBISGateway()
    return gateway.get_standard_details(is_code)


@app.get("/api/v1/bis/qco/check")
def apisetu_check_qco(is_code: str):
    """NeGD API Setu endpoint: statutory QCO mandatory certification status."""
    gateway: APISetuBISGateway = STATE.get("apisetu_gateway")
    if not gateway:
        gateway = APISetuBISGateway()
    return gateway.check_qco_compliance(is_code)


# Harvest pipeline of record; see src/ingestion/harvest_national_catalog.py.
REGISTRY_SOURCE = (
    "archive.org \u00b7 collection:publicsafetycode / gov.in.is "
    "(Indian Standards mirror); QCO notifications from bis.gov.in Scheme-I and crsbis.in"
)


@app.get("/api/registry-stats")
def registry_stats():
    """Read-only registry counts for the console. Cached after first call."""
    cached = STATE.get("registry_stats")
    if cached is not None:
        return cached

    # Normalizes the messy scheme_type strings into the three BIS scheme families.
    scheme_case = """
        CASE WHEN scheme_type LIKE 'Scheme-II %' OR scheme_type LIKE 'Scheme-II(%'
                  THEN 'Scheme-II (CRS)'
             WHEN scheme_type LIKE 'Scheme-IV%' THEN 'Scheme-IV (Hallmarking)'
             WHEN scheme_type LIKE 'Scheme-I%'  THEN 'Scheme-I (ISI Mark)'
             ELSE 'Other' END
    """
    badge_case = scheme_case.replace("scheme_type", "r.scheme_type") \
        .replace("'Scheme-II (CRS)'", "'CRS'") \
        .replace("'Scheme-IV (Hallmarking)'", "'Hallmarking'") \
        .replace("'Scheme-I (ISI Mark)'", "'ISI'")
    title_expr = "COALESCE(NULLIF(TRIM(s.title),''), r.product_category)"

    conn = get_connection()
    try:
        cur = conn.cursor()
        total = cur.execute("SELECT COUNT(*) FROM standards_registry").fetchone()[0]
        qco_total = cur.execute(
            "SELECT COUNT(*) FROM qco_compliance_rules WHERE is_mandatory=1").fetchone()[0]

        schemes = [
            {"scheme": r[0], "count": r[1]}
            for r in cur.execute(
                f"SELECT {scheme_case} AS fam, COUNT(*) FROM qco_compliance_rules "
                "WHERE is_mandatory=1 GROUP BY fam ORDER BY COUNT(*) DESC").fetchall()
        ]

        divisions = [
            {"name": r[0], "count": r[1]}
            for r in cur.execute(
                "SELECT division, COUNT(*) FROM standards_registry "
                "WHERE division IS NOT NULL AND TRIM(division) <> '' "
                "GROUP BY division ORDER BY COUNT(*) DESC LIMIT 8").fetchall()
        ]

        # Balanced across scheme families so every badge type is represented.
        samples = []
        for badge, limit in (("Hallmarking", 2), ("CRS", 2), ("ISI", 2)):
            rows = cur.execute(
                f"SELECT r.is_code, {title_expr} AS title, {badge_case} AS badge, r.order_name "
                "FROM qco_compliance_rules r "
                "LEFT JOIN standards_registry s ON s.is_code = r.is_code "
                f"WHERE r.is_mandatory=1 AND TRIM(COALESCE({title_expr},'')) <> '' "
                f"AND ({badge_case}) = ? ORDER BY LENGTH(title) ASC, r.is_code",
                (badge,)).fetchall()
            
            valid_rows = []
            for r in rows:
                code = r[0]
                if not any(c.isdigit() for c in code) or code.count('(') != code.count(')'):
                    continue
                valid_rows.append(r)
                if len(valid_rows) == limit:
                    break

            samples.extend(
                {"is_code": r[0], "title": r[1], "scheme": r[2], "order_name": r[3]}
                for r in valid_rows
            )
    finally:
        conn.close()

    # Provenance. snapshot_date and coverage are computed live; REGISTRY_SOURCE is a
    # constant describing the harvest pipeline (see ingestion/harvest_national_catalog.py).
    conn2 = get_connection()
    try:
        c2 = conn2.cursor()
        snapshot = c2.execute("SELECT MAX(created_at) FROM standards_registry").fetchone()[0]
        with_year = c2.execute(
            "SELECT COUNT(*) FROM standards_registry WHERE revision IS NOT NULL "
            "AND TRIM(revision) <> ''").fetchone()[0]
        superseded = c2.execute(
            "SELECT COUNT(*) FROM standards_registry WHERE status = 'SUPERSEDED'").fetchone()[0]
    finally:
        conn2.close()

    provenance = {
        "source": REGISTRY_SOURCE,
        "snapshot_date": (snapshot or "").split(" ")[0] or None,
        "snapshot_date_basis": (
            "latest created_at ingestion timestamp in standards_registry" if snapshot else None
        ),
        "edition_coverage": (
            f"revision field populated on {with_year:,} of {total:,} records"
        ),
        "supersession_coverage": (
            f"{superseded:,} of {total:,} records carry a SUPERSEDED status; "
            "the remainder default to ACTIVE and are not individually verified"
        ),
    }

    resolver = EditionResolver.get_instance()
    edition_link_count = resolver.multi_edition_count if resolver else 0

    payload = {
        "edition_link_count": edition_link_count,
        "data_provenance": provenance,
        "total_standards": total,
        "qco_notified_count": qco_total,
        "scheme_count": len(schemes),
        "scheme_breakdown": schemes,
        "divisions": divisions,
        "qco_samples": samples,
    }
    STATE["registry_stats"] = payload
    return payload


@app.get("/api/v1/bis/standards/{is_code}/allied")
def apisetu_get_allied(is_code: str):
    """NeGD API Setu endpoint: allied and normative reference standards."""
    gateway: APISetuBISGateway = STATE.get("apisetu_gateway")
    if not gateway:
        gateway = APISetuBISGateway()
    return gateway.get_allied_standards(is_code)


# --- Export Endpoint ---
from src.api.export_router import router as export_router
app.include_router(export_router, prefix="/api")
