"""FAISS Dense Vector Indexer for Indian Standards.

Maintains an IndexFlatIP index over 1024-d normalized BGE-M3 embeddings,
mapping FAISS integer slots to canonical IS codes and supporting fast persistence.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from src.retrieval.bge_multilingual_embedder import encode_texts


@dataclass
class DenseHit:
    is_code: str
    title: str
    dense_score: float
    rank: int


class FAISSDenseIndex:
    def __init__(self, is_codes: list[str], titles: list[str], index: faiss.IndexFlatIP):
        self.is_codes = is_codes
        self.titles = titles
        self.index = index

    def search(self, query_vec: np.ndarray, top_k: int = 25) -> list[DenseHit]:
        """Searches the dense index with a 1024-d query vector."""
        if query_vec.ndim == 1:
            query_vec = query_vec.reshape(1, -1)
        query_vec = query_vec.astype(np.float32)

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vec, k)

        hits = []
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0]), start=1):
            if idx < 0:
                continue
            hits.append(DenseHit(
                is_code=self.is_codes[idx],
                title=self.titles[idx],
                dense_score=float(score),
                rank=rank,
            ))
        return hits

    def save(self, index_dir: Path):
        """Saves the FAISS index binary and metadata mapping."""
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_dir / "dense_index.faiss"))
        meta = {"is_codes": self.is_codes, "titles": self.titles}
        (index_dir / "dense_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, index_dir: Path) -> FAISSDenseIndex:
        """Loads a persisted FAISS index and metadata."""
        faiss_path = index_dir / "dense_index.faiss"
        if not faiss_path.exists():
            # Check alternative filename
            faiss_path = index_dir / "bge_m3_dense.faiss"
        meta_path = index_dir / "dense_metadata.json"
        if not meta_path.exists():
            meta_path = index_dir / "standards_meta.json"

        if not faiss_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"FAISS index artifacts not found at {index_dir}")

        index = faiss.read_index(str(faiss_path))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

        if isinstance(meta, list):
            is_codes = [m["is_code"] for m in meta]
            titles = [m.get("title", "") for m in meta]
        else:
            is_codes = meta["is_codes"]
            titles = meta["titles"]

        return cls(is_codes, titles, index)


def build_faiss_index(standards: list[dict[str, Any]], output_dir: Path, batch_size: int = 16) -> FAISSDenseIndex:
    """Encodes standards and builds an exact Inner Product FAISS index."""
    is_codes = []
    titles = []
    texts_to_encode = []

    for s in standards:
        is_code = s["is_code"]
        title = s.get("title", "")
        scope = s.get("scope", "")
        # Enrich text representation for dense retrieval
        enriched_text = f"Indian Standard {is_code}: {title}. Scope: {scope}"
        is_codes.append(is_code)
        titles.append(title)
        texts_to_encode.append(enriched_text)

    # Generate embeddings via BGE-M3
    embeddings = encode_texts(texts_to_encode, batch_size=batch_size, show_progress_bar=True)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    dense_obj = FAISSDenseIndex(is_codes, titles, index)
    dense_obj.save(output_dir)
    return dense_obj
