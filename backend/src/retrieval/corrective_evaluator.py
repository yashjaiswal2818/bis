"""Corrective Retrieval-Augmented Generation (CRAG) Evaluator & Knowledge Refiner.

Implements domain-adapted CRAG for Indian Standards recommendation:
1. Retrieval Confidence Grading: Evaluates retrieved standards as CORRECT, AMBIGUOUS, or INCORRECT.
2. Knowledge Refinement (Decompose-then-Recompose): Splits voluminous standard scopes
   into fine-grained knowledge strips, filters out historical/bureaucratic noise, and extracts
   the single most relevant clause/application sentence for the tender query.
3. Allied Standards Graph Fallback: Queries SQLite cross-references when confidence is ambiguous.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class KnowledgeStrip:
    clause_text: str
    relevance_score: float
    is_grounded: bool


class CorrectiveEvaluator:
    """Evaluates candidate relevance and extracts grounded knowledge strips."""

    # Common BIS bureaucratic and adoption boilerplate patterns to strip
    BOILERPLATE_PATTERNS = [
        r"^this\s+indian\s+standard\s+(?:\([^\)]+\)\s+)?(?:was\s+adopted|is\s+adopted|has\s+been\s+adopted).*?(?:after\s+the\s+draft|by\s+the\s+bureau|approved\s+by).*?(?:\.|\;)",
        r"^this\s+standard\s+was\s+originally\s+published\s+in\s+\d{4}.*?(?:\.|\;)",
        r"^in\s+this\s+(?:first|second|third|fourth|fifth|sixth)?\s*revision.*?(?:\.|\;)",
        r"^for\s+the\s+purpose\s+of\s+deciding\s+whether\s+a\s+particular\s+requirement.*?(?:\.|\;)",
        r"^a\s+scheme\s+for\s+labelling\s+environment\s+friendly\s+products.*?(?:\.|\;)",
        r"^while\s+preparing\s+this\s+standard,\s+assistance\s+has\s+been\s+derived.*?(?:\.|\;)",
    ]

    STOP_WORDS = {
        "this", "that", "these", "those", "indian", "standard", "standards", "is",
        "specification", "prescribes", "covers", "specifies", "requirements", "shall",
        "with", "from", "into", "during", "under", "over", "such", "than", "other",
        "method", "methods", "test", "testing", "general", "purposes", "grade",
        "product", "manufacture", "chemical", "physical", "code", "practice"
    }

    @classmethod
    def clean_scope_text(cls, scope: str) -> str:
        """Removes introductory BIS adoption boilerplate from scope text."""
        cleaned = scope.strip()
        for pattern in cls.BOILERPLATE_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned

    @classmethod
    def decompose_scope_to_strips(cls, scope: str, title: str = "") -> list[str]:
        """Deconstructs scope text into individual sentence/clause strips."""
        clean_text = cls.clean_scope_text(scope)
        if not clean_text:
            return [title] if title else []

        # Split on sentence boundaries, numbered clauses, or semicolons
        raw_sentences = re.split(r"(?<=[.!?])\s+|\n+|(?<=[;])\s+", clean_text)
        strips = []
        for s in raw_sentences:
            s_clean = s.strip()
            # Filter out very short or purely procedural fragments
            if len(s_clean) >= 20 and not any(p in s_clean.lower() for p in [
                "was adopted by the bureau",
                "assistance has been derived",
                "finalized by the",
                "rules and regulations",
            ]):
                strips.append(s_clean)

        if not strips and clean_text:
            strips.append(clean_text[:300])
        return strips

    @classmethod
    def extract_knowledge_strip(
        cls,
        query: str,
        is_code: str,
        title: str,
        scope: str,
        detected_grades: set[str] | None = None,
        detected_materials: set[str] | None = None,
    ) -> str:
        """Extracts the single most precise, relevant knowledge strip from a standard's scope.
        
        Uses decompose-then-recompose to eliminate irrelevant filler and return the exact
        clause or application requirement that matches the tender specifications.
        """
        strips = cls.decompose_scope_to_strips(scope, title)
        if not strips:
            return f"{is_code} ({title})"

        # Extract meaningful query keywords
        q_tokens = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", query.lower())) - cls.STOP_WORDS
        title_tokens = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", title.lower())) - cls.STOP_WORDS
        grades = {g.lower() for g in (detected_grades or set())}
        materials = {m.lower().replace("_", " ") for m in (detected_materials or set())}

        scored_strips: list[tuple[str, float]] = []
        for s in strips:
            s_lower = s.lower()
            s_tokens = set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", s_lower))

            # Base keyword overlap
            overlap = len(s_tokens.intersection(q_tokens))
            score = overlap * 1.5

            # High-priority entity matches
            for g in grades:
                if g in s_lower:
                    score += 4.0
            for m in materials:
                if m in s_lower:
                    score += 3.0

            # Title alignment
            title_overlap = len(s_tokens.intersection(title_tokens))
            score += title_overlap * 0.5

            # Factual application cues
            if any(cue in s_lower for cue in ["intended for", "applicable to", "applies to", "specifies the", "covers the", "suitable for"]):
                score += 1.0

            scored_strips.append((s, score))

        # Select highest-scoring knowledge strip
        scored_strips.sort(key=lambda x: x[1], reverse=True)
        best_strip, best_score = scored_strips[0]

        # Truncate slightly if overly verbose while preserving whole sentences
        if len(best_strip) > 280:
            best_strip = best_strip[:277].rsplit(" ", 1)[0] + "..."

        return best_strip

    @classmethod
    def grade_confidence(
        cls,
        rerank_score: float,
        is_direct_match: bool = False,
        has_schedule_match: bool = False,
        precision_alignment: float = 0.0,
    ) -> str:
        """Assigns calibrated CRAG confidence verdict: 'HIGH', 'MEDIUM', or 'LOW'."""
        if is_direct_match or has_schedule_match:
            return "HIGH"
        from src.retrieval.hybrid_search_orchestrator import get_confidence_band
        effective_score = rerank_score + (0.5 * precision_alignment)
        return get_confidence_band(effective_score)

    @classmethod
    def get_allied_fallback(
        cls,
        is_code: str,
        db_path: Path | str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Queries the SQLite knowledge graph for allied and parent standards when ambiguous."""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            query = """
                SELECT target_standard, edge_type, frequency 
                FROM allied_standards_edges 
                WHERE source_standard = ? OR source_standard = ?
                ORDER BY frequency DESC 
                LIMIT ?
            """
            base_code = re.sub(r":\s*\d{4}.*", "", is_code).strip()
            cursor.execute(query, (is_code, base_code, limit))
            rows = cursor.fetchall()
            conn.close()
            return [{"target_standard": r[0], "edge_type": r[1], "weight": r[2]} for r in rows]
        except Exception:
            return []
