"""Hybrid Search Orchestrator for Indian Standards.

Fuses BM25 sparse retrieval and FAISS dense vector retrieval via
Reciprocal Rank Fusion (RRF), reranks candidates with bge-reranker-v2-m3,
applies the hard IS-code whitelist guard, and enriches results with SQLite QCO and allied data.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.database.sqlite_manager import get_standard_details, normalize_is_code
from src.retrieval.bge_multilingual_embedder import encode_query_cached
from src.retrieval.bm25_lexical_indexer import BM25LexicalIndex
from src.retrieval.cross_encoder_reranker import auto_clamp_rerank_pool, rerank_pairs
from src.retrieval.faiss_vector_indexer import FAISSDenseIndex

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


def get_confidence_band(score: float) -> str:
    """Calibrated confidence bands based on benchmark testing."""
    if score >= 0.55:
        return "HIGH"
    elif score >= 0.40:
        return "MEDIUM"
    return "LOW"


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
                self.whitelist = {normalize_is_code(c) for c in codes if isinstance(c, str)}
            except Exception as e:
                print(f"[Warning] Error loading whitelist: {e}", file=sys.stderr)

        # Also seed whitelist with all verified standard codes from SQLite registry
        try:
            from src.database.sqlite_manager import get_connection
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT is_code FROM standards_registry")
                db_codes = [r[0] for r in cur.fetchall()]
                self.whitelist.update({normalize_is_code(c) for c in db_codes})
        except Exception:
            pass

    def search(self, query: str, top_k: int | None = None) -> list[RecommendedStandard]:
        """Executes full hybrid search pipeline for a procurement query."""
        if top_k is None:
            top_k = self.final_k

        # 1. Dense retrieval via BGE-M3
        query_vec = encode_query_cached(query)
        dense_hits = self.dense_index.search(query_vec, top_k=self.dense_k)

        # 2. Lexical retrieval via BM25
        bm25_hits = self.bm25_index.search(query, top_k=self.bm25_k)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: dict[str, float] = {}
        standard_metadata: dict[str, dict[str, Any]] = {}

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

        # Sort by combined RRF score
        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # 4. Filter by anti-hallucination whitelist
        if self.whitelist:
            sorted_candidates = [
                c for c in sorted_candidates if normalize_is_code(c[0]) in self.whitelist
            ]

        # Take pool for cross-encoder reranker
        rerank_pool = sorted_candidates[:self.rerank_k]
        if not rerank_pool:
            return []

        # 5. Cross-Encoder Reranking
        passages = []
        for code, _ in rerank_pool:
            details = get_standard_details(code)
            scope_text = str((details.get("scope") if details else "") or "")
            title = str(standard_metadata.get(code, {}).get("title", ""))
            passages.append(f"{code} {title}. {scope_text[:300]}")

        rerank_scores = rerank_pairs(query, passages)

        # Pair candidates with their rerank scores
        reranked = []
        for (code, rrf_score), r_score in zip(rerank_pool, rerank_scores):
            reranked.append((code, rrf_score, r_score))

        # Re-sort by cross-encoder score
        reranked.sort(key=lambda x: x[2], reverse=True)

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
            ))

        return final_results
