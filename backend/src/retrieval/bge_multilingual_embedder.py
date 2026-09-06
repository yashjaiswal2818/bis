"""BGE-M3 Multilingual Dense Embedder for Indian Standards.

Wraps BAAI/bge-m3 dense representation (1024 dimensions), with support
for CPU execution, query encoding cache, and batch encoding.
"""
from __future__ import annotations

import os

# Prevent symlink stalls on Windows with unauthenticated HuggingFace requests
os.environ["HF_HUB_DISABLE_XET"] = "1"

from functools import lru_cache
from typing import Sequence

import numpy as np

MODEL_NAME = "BAAI/bge-m3"
_MODEL_INSTANCE = None


def get_embedder():
    """Singleton getter for SentenceTransformer embedder on CPU or CUDA."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        from sentence_transformers import SentenceTransformer
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Force offline cache if already downloaded
        _MODEL_INSTANCE = SentenceTransformer(MODEL_NAME, device=device)
    return _MODEL_INSTANCE


def encode_texts(texts: Sequence[str], batch_size: int = 16, show_progress_bar: bool = False) -> np.ndarray:
    """Encodes a sequence of texts into L2-normalized 1024-d float32 vectors."""
    model = get_embedder()
    embeddings = model.encode(
        list(texts),
        batch_size=batch_size,
        show_progress_bar=show_progress_bar,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return embeddings.astype(np.float32)


@lru_cache(maxsize=512)
def encode_query_cached(query: str) -> np.ndarray:
    """Caches query vectors in memory to ensure sub-millisecond repeated lookups."""
    model = get_embedder()
    vec = model.encode(
        query,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vec.astype(np.float32)


def warmup():
    """Warms up the embedder model once at application startup."""
    encode_query_cached("warmup query for ordinary portland cement")
