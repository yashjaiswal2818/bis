"""BM25 Lexical Indexer for Indian Standards.

Handles domain-aware tokenization (preserving IS-codes, grades, and alphanumeric patterns)
and performs BM25 Okapi retrieval over standards titles, scopes, and descriptions.
"""
from __future__ import annotations

import json
import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

TOKEN_RE = re.compile(r"\b[a-z0-9]+(?:[-_][a-z0-9]+)*\b", re.IGNORECASE)


def tokenize_text(text: str) -> list[str]:
    """Tokenizes text while preserving alphanumeric identifiers (e.g., 'is456', 'fe500d')."""
    if not text:
        return []
    # Standardize IS code patterns: "IS 269" -> "is269"
    standardized = re.sub(r"\bis\s*(\d+)\b", r"is\1 is \1", text, flags=re.IGNORECASE)
    tokens = [t.lower() for t in TOKEN_RE.findall(standardized)]
    return tokens


@dataclass
class BM25Hit:
    is_code: str
    title: str
    bm25_score: float
    rank: int


class BM25LexicalIndex:
    is_codes: list[str]
    titles: list[str]
    bm25: BM25Okapi

    def __init__(self, is_codes: list[str], titles: list[str], corpus_tokens: list[list[str]]):
        self.is_codes = is_codes
        self.titles = titles
        self.bm25 = BM25Okapi(corpus_tokens)

    def search(self, query: str, top_k: int = 25) -> list[BM25Hit]:
        """Searches BM25 index and returns top-K candidates."""
        q_tokens = tokenize_text(query)
        if not q_tokens:
            return []

        # Enhance query tokens: expand adjacent tokens into hyphenated compounds (e.g. "ready mixed" -> "ready-mixed")
        # and split existing hyphenated tokens (e.g. "ready-mixed" -> "ready", "mixed")
        expanded_tokens = list(q_tokens)
        if hasattr(self.bm25, "idf"):
            for i in range(len(q_tokens) - 1):
                pair = f"{q_tokens[i]}-{q_tokens[i+1]}"
                if pair in self.bm25.idf:
                    expanded_tokens.append(pair)
        for tok in q_tokens:
            if "-" in tok:
                for sub_tok in tok.split("-"):
                    if sub_tok and sub_tok not in expanded_tokens:
                        expanded_tokens.append(sub_tok)

        scores = self.bm25.get_scores(expanded_tokens)
        top_indices = scores.argsort()[::-1][:top_k]

        hits = []
        for rank, idx in enumerate(top_indices, start=1):
            score = float(scores[idx])
            if score <= 0.0:
                break
            hits.append(BM25Hit(
                is_code=self.is_codes[idx],
                title=self.titles[idx],
                bm25_score=score,
                rank=rank,
            ))
        return hits

    def save(self, index_path: Path):
        """Persists the BM25 index to disk."""
        index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(index_path, "wb") as f:
            pickle.dump({
                "is_codes": self.is_codes,
                "titles": self.titles,
                "bm25": self.bm25,
            }, f)

    @classmethod
    def load(cls, index_path: Path) -> BM25LexicalIndex:
        """Loads a persisted BM25 index from disk."""
        if not index_path.exists():
            # Check alternative filename
            alt = index_path.parent / "bm25.pkl"
            if alt.exists():
                index_path = alt

        with open(index_path, "rb") as f:
            data = pickle.load(f)
        obj = cls.__new__(cls)

        if "is_codes" in data and "titles" in data:
            obj.is_codes = data["is_codes"]
            obj.titles = data["titles"]
            obj.bm25 = data["bm25"]
        else:
            # Precomputed format from BIS-COMPASS: load companion metadata
            meta_path = index_path.parent / "dense_metadata.json"
            if not meta_path.exists():
                meta_path = index_path.parent / "standards_meta.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(meta, list):
                obj.is_codes = [m["is_code"] for m in meta]
                obj.titles = [m.get("title", "") for m in meta]
            else:
                obj.is_codes = meta["is_codes"]
                obj.titles = meta["titles"]
            obj.bm25 = data["bm25"]

        return obj


def build_bm25_index(standards: list[dict[str, Any]], output_path: Path) -> BM25LexicalIndex:
    """Builds a BM25 index with title boosting (repeating titles 3x)."""
    is_codes = []
    titles = []
    corpus_tokens = []

    for s in standards:
        is_code = s["is_code"]
        title = s.get("title", "")
        scope = s.get("scope", "")
        full_text = s.get("full_text", "")

        # Title boosting: repeat title 3 times to prioritize direct name matches
        enriched_doc = f"{is_code} {title} {title} {title} {scope} {full_text[:1000]}"
        tokens = tokenize_text(enriched_doc)

        is_codes.append(is_code)
        titles.append(title)
        corpus_tokens.append(tokens)

    index = BM25LexicalIndex(is_codes, titles, corpus_tokens)
    index.save(output_path)
    return index
