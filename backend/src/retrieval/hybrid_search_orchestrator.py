"""Hybrid Search Orchestrator for Indian Standards.

Fuses BM25 sparse retrieval and FAISS dense vector retrieval via
Reciprocal Rank Fusion (RRF), reranks candidates with bge-reranker-v2-m3,
applies the hard IS-code whitelist guard, and enriches results with SQLite QCO and allied data.
"""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.database.sqlite_manager import (
    extract_base_code,
    get_standard_details,
    normalize_is_code,
)
from src.retrieval.bge_multilingual_embedder import encode_query_cached
from src.retrieval.bm25_lexical_indexer import BM25LexicalIndex
from src.retrieval.cross_encoder_reranker import auto_clamp_rerank_pool, rerank_pairs
from src.retrieval.faiss_vector_indexer import FAISSDenseIndex
from src.retrieval.query_preprocessor import AdaptiveQueryPreprocessor, ProcessedQuery

INDEX_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "index"
WHITELIST_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "is_code_whitelist.json"


@dataclass
class RecommendedStandard:
    rank: int
    is_code: str
    title: str
    scope: str
    rerank_score: float
    rrf_score: float
    confidence: str  # 'HIGH' | 'MEDIUM' | 'LOW'
    status: str      # 'ACTIVE' | 'SUPERSEDED'
    superseded_by: str | None = None
    qco_rules: list[dict[str, Any]] = field(default_factory=list)
    allied_standards: list[dict[str, Any]] = field(default_factory=list)
    reaffirmation_year: int | None = None
    amendments_count: int = 0


def get_confidence_band(score: float) -> str:
    """Calibrated confidence bands based on benchmark testing."""
    if score >= 0.55:
        return "HIGH"
    elif score >= 0.40:
        return "MEDIUM"
    return "LOW"


def compute_precision_alignment(
    query: str,
    title: str,
    is_code: str,
    intent: str,
    detected_grades: set[str] | None = None,
    detected_parts: set[str] | None = None,
    detected_materials: set[str] | None = None,
) -> float:
    """Computes exact title, grade, part, material, and intent alignment score."""
    score = 0.0
    doc_text = f"{is_code} {title}".lower()

    # 1. Grade matching / mismatching
    q_grades = detected_grades if detected_grades is not None else AdaptiveQueryPreprocessor.extract_grades(query)
    doc_grades = AdaptiveQueryPreprocessor.extract_grades(doc_text)
    if q_grades:
        matched_grades = q_grades.intersection(doc_grades)
        if matched_grades:
            score += 0.25 * len(matched_grades)
        else:
            # Penalize competing cement grades (e.g. Query has 33 Grade, doc has 43 or 53 Grade)
            cement_grades = {"33grade", "43grade", "53grade"}
            if q_grades.intersection(cement_grades) and doc_grades.intersection(cement_grades):
                score -= 0.25

    # 2. Part matching (e.g. Part 1 vs Part 2)
    q_parts = detected_parts if detected_parts is not None else AdaptiveQueryPreprocessor.extract_parts(query)
    doc_parts = AdaptiveQueryPreprocessor.extract_parts(doc_text)
    if q_parts:
        if q_parts.intersection(doc_parts):
            score += 0.30
        elif doc_parts:
            score -= 0.25

    # 3. Material Specificity Guard (prevents ordinary cement from displacing slag/calcined clay/supersulphated)
    materials = detected_materials if detected_materials is not None else AdaptiveQueryPreprocessor.detect_materials(query)
    if materials:
        if "slag_cement" in materials:
            if "slag" in doc_text or "455" in is_code:
                score += 0.35
            elif "ordinary" in doc_text:
                score -= 0.25
        if "calcined_clay" in materials:
            if "calcined clay" in doc_text or ("1489" in is_code and "part 2" in doc_text):
                score += 0.35
            elif "fly ash" in doc_text:
                score -= 0.25
        if "fly_ash" in materials:
            if "fly ash" in doc_text or ("1489" in is_code and "part 1" in doc_text):
                score += 0.35
        if "supersulphated" in materials:
            if "supersulphated" in doc_text or "6909" in is_code:
                score += 0.35
        if "white_cement" in materials:
            if "white" in doc_text or "8042" in is_code:
                score += 0.35
        if "deformed_bars" in materials:
            if "deformed" in doc_text or "1786" in is_code:
                score += 0.35
            elif "general structural" in doc_text:
                score -= 0.20
        if "asbestos_sheets" in materials:
            if "asbestos" in doc_text or "459" in is_code:
                score += 0.35
        if "concrete_pipes" in materials:
            if "pipe" in doc_text or "458" in is_code:
                score += 0.35
        if "concrete_blocks" in materials:
            if "block" in doc_text or "2185" in is_code:
                score += 0.35
        if "aggregates" in materials:
            if "aggregate" in doc_text or "383" in is_code:
                score += 0.35
        if "drinking_water" in materials:
            if "drinking water" in doc_text or "10500" in is_code:
                score += 0.35

    # 4. Title keyword overlap boost (excluding procedural boilerplate words)
    stop_words = {
        "standard", "indian", "specification", "requirements", "covers", "grade",
        "product", "manufacture", "chemical", "physical", "code", "practice",
        "general", "purposes", "method", "methods", "test", "testing"
    }
    title_words = set(re.findall(r"\b[a-z]{4,}\b", title.lower())) - stop_words
    query_words = set(re.findall(r"\b[a-z]{4,}\b", query.lower())) - stop_words
    meaningful_overlap = title_words.intersection(query_words)
    if meaningful_overlap:
        score += min(len(meaningful_overlap) * 0.05, 0.25)

    # 5. Intent alignment
    title_lower = title.lower()
    if intent == "SPECIFICATION":
        if "specification" in title_lower or "specification" in is_code.lower():
            score += 0.05
        elif any(t in title_lower for t in ["method of test", "sampling", "determination", "analysis"]):
            score -= 0.20  # Penalize test methods when user wants product specification
    elif intent == "TEST_METHOD":
        if any(t in title_lower for t in ["method of test", "testing", "sampling", "determination", "analysis"]):
            score += 0.30
    elif intent == "CODE_OF_PRACTICE":
        if "code of practice" in title_lower:
            score += 0.30

    return score


class HybridSearchOrchestrator:
    def __init__(
        self,
        index_dir: Path = INDEX_DIR,
        whitelist_path: Path = WHITELIST_PATH,
        dense_k: int = 25,
        bm25_k: int = 25,
        rerank_k: int = 25,
        final_k: int = 5,
        rrf_c: int = 60,
    ):
        self.dense_index = FAISSDenseIndex.load(index_dir)
        self.bm25_index = BM25LexicalIndex.load(index_dir / "bm25_index.pkl")
        self.dense_k = dense_k
        self.bm25_k = bm25_k
        self.rerank_k = auto_clamp_rerank_pool(rerank_k)
        self.final_k = final_k
        self.rrf_c = rrf_c

        # Load anti-hallucination whitelist
        self.whitelist: set[str] = set()
        if whitelist_path.exists():
            try:
                data = json.loads(whitelist_path.read_text(encoding="utf-8"))
                codes = []
                if isinstance(data, dict):
                    codes.extend(data.get("canonical", []))
                    codes.extend(data.get("normalized", []))
                    # Fallback for any other list values
                    for v in data.values():
                        if isinstance(v, list):
                            codes.extend(v)
                elif isinstance(data, list):
                    codes.extend(data)
                for c in codes:
                    if isinstance(c, str):
                        self.whitelist.add(normalize_is_code(c))
                        self.whitelist.add(extract_base_code(c))
            except Exception as e:
                print(f"[Warning] Error loading whitelist: {e}", file=sys.stderr)

        # Also seed whitelist with all verified standard codes from SQLite registry
        try:
            from src.database.sqlite_manager import get_connection
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT is_code, is_code_norm, base_code FROM standards_registry")
                for r in cur.fetchall():
                    self.whitelist.add(normalize_is_code(r[0]))
                    if len(r) > 1 and r[1]:
                        self.whitelist.add(r[1])
                    if len(r) > 2 and r[2]:
                        self.whitelist.add(r[2])
        except Exception:
            pass

    def search(self, query: str, top_k: int | None = None) -> list[RecommendedStandard]:
        """Executes full hybrid search pipeline with precision ranking for a procurement query."""
        if top_k is None:
            top_k = self.final_k

        # 0. Adaptive Query Processing & Normalization
        processed = AdaptiveQueryPreprocessor.process(query)
        intent = processed.intent
        clean_q = processed.cleaned_query
        bm25_q = processed.bm25_expanded_query
        # Lookup and verify details for direct IS codes against master catalog
        valid_direct_matches = []
        for raw_match in processed.direct_is_codes:
            details = get_standard_details(raw_match)
            if details and details.get("is_code"):
                valid_direct_matches.append(details["is_code"])
            elif normalize_is_code(raw_match) in self.whitelist or extract_base_code(raw_match) in self.whitelist:
                valid_direct_matches.append(raw_match)
        direct_matches = list(set(valid_direct_matches))

        # 1. Dense retrieval via BGE-M3 (clean query first to avoid vector dilution)
        query_vec = encode_query_cached(clean_q)
        dense_hits = self.dense_index.search(query_vec, top_k=self.dense_k)

        # Also retrieve with raw query if informative and merge top dense results
        if clean_q != query and len(query) >= 8:
            raw_vec = encode_query_cached(query)
            raw_dense_hits = self.dense_index.search(raw_vec, top_k=self.dense_k)
            seen_dense = {h.is_code: h for h in dense_hits}
            for rh in raw_dense_hits:
                if rh.is_code not in seen_dense:
                    dense_hits.append(rh)
                elif rh.dense_score > seen_dense[rh.is_code].dense_score:
                    seen_dense[rh.is_code].dense_score = rh.dense_score
            dense_hits.sort(key=lambda x: x.dense_score, reverse=True)
            for idx, h in enumerate(dense_hits, start=1):
                h.rank = idx

        # 2. Lexical retrieval via BM25 using expanded domain query
        bm25_hits = self.bm25_index.search(bm25_q, top_k=self.bm25_k)
        if clean_q != bm25_q and len(clean_q) >= 4:
            clean_bm25_hits = self.bm25_index.search(clean_q, top_k=self.bm25_k)
            seen_bm25 = {h.is_code: h for h in bm25_hits}
            for ch in clean_bm25_hits:
                if ch.is_code not in seen_bm25:
                    bm25_hits.append(ch)
                elif ch.bm25_score > seen_bm25[ch.is_code].bm25_score:
                    seen_bm25[ch.is_code].bm25_score = ch.bm25_score
            bm25_hits.sort(key=lambda x: x.bm25_score, reverse=True)
            for idx, h in enumerate(bm25_hits, start=1):
                h.rank = idx

        # Console Diagnostic Logging: Display Vector vs Vectorless results separately
        print("\n" + "=" * 80)
        print(f"SEARCH QUERY: \"{query}\"")
        if clean_q != query:
            print(f"ADAPTIVE FOCUS: \"{clean_q}\" (Intent: {intent}, Grades: {processed.detected_grades}, Materials: {processed.detected_materials})")
        print(f"BM25 EXPANDED: \"{bm25_q}\"")
        print("-" * 80)
        print(f">> [1. VECTOR PIPELINE - FAISS / BGE-M3] Top {min(len(dense_hits), 8)} Hits:")
        if dense_hits:
            for h in dense_hits[:8]:
                print(f"   [{h.rank:2d}] {h.is_code:<24} | Sim: {h.dense_score:.4f} | {h.title[:45]}")
        else:
            print("   (No dense vector hits)")

        print(f"\n>> [2. VECTORLESS PIPELINE - BM25 Lexical] Top {min(len(bm25_hits), 8)} Hits:")
        if bm25_hits:
            for h in bm25_hits[:8]:
                print(f"   [{h.rank:2d}] {h.is_code:<24} | BM25: {h.bm25_score:.4f} | {h.title[:45]}")
        else:
            print("   (No lexical BM25 hits)")

        if direct_matches:
            print(f"\n>> [DIRECT CODE MATCH DETECTED]: {', '.join(direct_matches)}")
        print("=" * 80)

        # 2.5 Zero-Hallucination Relevance Gate: Protect against invalid/unrelated queries
        max_dense = max((h.dense_score for h in dense_hits), default=0.0)
        max_bm25 = max((h.bm25_score for h in bm25_hits), default=0.0)

        has_verified_code = bool(direct_matches)
        has_strong_dense = max_dense >= 0.46
        has_strong_bm25 = max_bm25 >= 30.0
        has_dual_signal = max_dense >= 0.43 and max_bm25 >= 22.0

        # Immediate rejection for unverified IS codes (e.g. IS 99999999) without extensive engineering text
        if processed.direct_is_codes and not direct_matches:
            if len(clean_q.split()) <= 4 or not (has_strong_bm25 or max_dense >= 0.60):
                print(f">> [RELEVANCE GATE] Explicit IS standard code {processed.direct_is_codes} not found in BIS master catalog. Rejecting 0 hits.")
                print("=" * 80 + "\n")
                return []

        if not (has_verified_code or has_strong_dense or has_strong_bm25 or has_dual_signal):
            print(f">> [RELEVANCE GATE] Query rejected as invalid / out-of-domain (Max Dense: {max_dense:.3f}, Max BM25: {max_bm25:.1f})")
            print("=" * 80 + "\n")
            return []

        # 3. Score-Aware Reciprocal Rank Fusion
        rrf_scores: dict[str, float] = {}
        standard_metadata: dict[str, dict[str, Any]] = {}

        max_dense_div = max_dense or 1.0
        max_bm25_div = max_bm25 or 1.0

        for hit in dense_hits:
            code = hit.is_code
            rrf_scores[code] = rrf_scores.get(code, 0.0) + 1.0 / (self.rrf_c + hit.rank)
            standard_metadata[code] = {"title": hit.title, "dense_score": hit.dense_score}

        for bm_hit in bm25_hits:
            code = bm_hit.is_code
            rrf_scores[code] = rrf_scores.get(code, 0.0) + 1.0 / (self.rrf_c + bm_hit.rank)
            if code not in standard_metadata:
                standard_metadata[code] = {"title": bm_hit.title, "dense_score": 0.0}
            standard_metadata[code]["bm25_score"] = bm_hit.bm25_score

        # Inject boosted score for direct code matches
        for direct_code in direct_matches:
            rrf_scores[direct_code] = rrf_scores.get(direct_code, 0.0) + 1.0
            if direct_code not in standard_metadata:
                d = get_standard_details(direct_code)
                standard_metadata[direct_code] = {
                    "title": d.get("title", "") if d else "",
                    "dense_score": 1.0,
                }

        # Calculate composite candidate score
        composite_candidates = []
        for code, rrf_val in rrf_scores.items():
            dense_norm = standard_metadata[code].get("dense_score", 0.0) / max_dense_div
            bm25_norm = standard_metadata[code].get("bm25_score", 0.0) / max_bm25_div
            title_text = standard_metadata[code].get("title", "")
            alignment = compute_precision_alignment(
                query=query,
                title=title_text,
                is_code=code,
                intent=intent,
                detected_grades=processed.detected_grades,
                detected_parts=processed.detected_parts,
                detected_materials=processed.detected_materials,
            )
            
            fused_score = rrf_val + (0.015 * bm25_norm) + (0.010 * dense_norm) + (0.020 * alignment)
            composite_candidates.append((code, rrf_val, fused_score, alignment))

        # Sort by composite score
        composite_candidates.sort(key=lambda x: x[2], reverse=True)

        # 4. Filter by anti-hallucination whitelist
        if self.whitelist:
            composite_candidates = [
                c for c in composite_candidates 
                if normalize_is_code(c[0]) in self.whitelist or extract_base_code(c[0]) in self.whitelist
            ]

        # Take pool for cross-encoder reranker
        rerank_pool = composite_candidates[:self.rerank_k]
        if not rerank_pool:
            return []

        # 5. Cross-Encoder Reranking
        passages = []
        for code, _, _, _ in rerank_pool:
            details = get_standard_details(code)
            scope_text = str((details.get("scope") if details else "") or "")
            title = str(standard_metadata.get(code, {}).get("title", "") or (details.get("title") if details else ""))
            passages.append(f"{code}: {title}. Scope: {scope_text[:800]}")

        # Use cleaned query to prevent conversational fluff from crowding out cross-attention tokens
        rerank_query = clean_q if len(clean_q) >= 6 else query
        rerank_scores = rerank_pairs(rerank_query, passages)

        # Pair candidates with their rerank scores and apply precision alignment
        reranked = []
        for (code, rrf_score, _, alignment), r_score in zip(rerank_pool, rerank_scores):
            details = get_standard_details(code) or {}
            status_boost = 0.03 if details.get("status") == "ACTIVE" else 0.0
            direct_boost = 0.35 if code in direct_matches else 0.0

            final_r_score = r_score + alignment + status_boost + direct_boost
            final_r_score = max(0.01, min(0.999, final_r_score))
            reranked.append((code, rrf_score, final_r_score))

        # Re-sort by cross-encoder final precision score
        reranked.sort(key=lambda x: x[2], reverse=True)

        # Filter out spurious candidates below relevance confidence floor
        reranked = [
            item for item in reranked
            if item[2] >= 0.38 or item[0] in direct_matches
        ]
        if not reranked:
            print(">> [RELEVANCE GATE] All candidate matches dropped below minimum confidence floor.")
            print("=" * 80 + "\n")
            return []

        # 6. Assemble final enriched recommendations
        final_results = []
        for rank, (code, rrf_score, r_score) in enumerate(reranked[:top_k], start=1):
            details = get_standard_details(code) or {}
            confidence = get_confidence_band(r_score)

            title_val = details.get("title") or standard_metadata.get(code, {}).get("title")
            title = str(title_val).strip() if title_val is not None else ""

            scope_val = details.get("scope")
            scope = str(scope_val).strip() if scope_val is not None else ""

            status_val = details.get("status")
            status = str(status_val).strip() if status_val is not None else "ACTIVE"

            final_results.append(RecommendedStandard(
                rank=rank,
                is_code=code,
                title=title,
                scope=scope,
                rerank_score=r_score,
                rrf_score=rrf_score,
                confidence=confidence,
                status=status,
                superseded_by=details.get("superseded_by"),
                qco_rules=details.get("qco_rules", []),
                allied_standards=details.get("allied_standards", []),
                reaffirmation_year=details.get("reaffirmation_year"),
                amendments_count=details.get("amendments_count", 0),
            ))

        print(f">> [FINAL FUSED & RERANKED SELECTION] Top {len(final_results)}:")
        for r in final_results:
            print(f"   #{r.rank} {r.is_code:<24} | Rerank: {r.rerank_score:.4f} | RRF: {r.rrf_score:.4f} | Conf: {r.confidence:<6} | {r.title[:40]}")
        print("=" * 80 + "\n")

        return final_results
