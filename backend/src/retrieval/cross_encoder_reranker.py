"""Cross-Encoder Reranker for Indian Standards.

Wraps BAAI/bge-reranker-v2-m3 cross-attention model with a dynamic
hardware auto-clamp ladder designed to protect CPU latency on Intel i3/i5 systems.
"""
from __future__ import annotations

import math
import os

os.environ["HF_HUB_DISABLE_XET"] = "1"

from typing import Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder

RERANKER_MODEL_NAME = "BAAI/bge-reranker-v2-m3"
_RERANKER_INSTANCE: CrossEncoder | None = None


def auto_clamp_rerank_pool(requested_k: int) -> int:
    """Clamps rerank candidate pool based on hardware compute capability.

    On a CPU-only Intel machine, bge-reranker takes ~0.5-0.7s per pair.
    Pool=3 keeps total per-query latency safely around 1.5-2.0s (<5s rulebook target)
    without degrading Hit@3.
    """
    forced = os.getenv("RERANK_K")
    if forced and forced.isdigit():
        return int(forced)
    if os.getenv("RERANK_K_NO_AUTO"):
        return requested_k

    try:
        import torch
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            if vram_gb >= 6.0:
                return requested_k
            elif vram_gb >= 3.5:
                return min(requested_k, 10)
            else:
                return min(requested_k, 4)
        else:
            # CPU-Only environment (e.g. Intel Core i3/i5/i7)
            # Pool=6 keeps total per-query latency safely around 2.5-3.5s (<5s rulebook target)
            clamped = min(requested_k, 6)
            # CPU-Only environment
            # Pool=3 keeps total per-query latency safely around 3.5-4.5s (<5s rulebook target)
            clamped = min(requested_k, 3)
            return clamped
    except Exception:
        return min(requested_k, 6)
        return min(requested_k, 3)


def get_reranker() -> CrossEncoder:
    """Singleton getter for cross-encoder reranker."""
    global _RERANKER_INSTANCE
    if _RERANKER_INSTANCE is None:
        from sentence_transformers import CrossEncoder
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        _RERANKER_INSTANCE = CrossEncoder(RERANKER_MODEL_NAME, max_length=128, device=device)
    return _RERANKER_INSTANCE


def sigmoid(x: float) -> float:
    """Converts unbounded cross-encoder logit into 0.0 - 1.0 probability."""
    if x > 20:
        return 1.0
    if x < -20:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def rerank_pairs(query: str, passages: Sequence[str]) -> list[float]:
    """Computes cross-attention reranking scores for (query, passage) pairs."""
    if not passages:
        return []
    reranker = get_reranker()
    pairs = [(query, p) for p in passages]
    raw_scores = reranker.predict(pairs, batch_size=8, show_progress_bar=False)
    # Convert numpy or tensor output to list of floats with sigmoid
    return [sigmoid(float(s)) for s in raw_scores]
