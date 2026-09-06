"""Model Pre-Downloader with format filtering to prevent huge 12 GB downloads.

Downloads only required safetensors weights for BGE-M3 and BGE-Reranker-v2-m3,
ignoring redundant ONNX, OpenVINO, Flax, and TensorFlow files.
"""
from __future__ import annotations

import os
import sys
import time

# Essential Windows flag to avoid symlink hanging
os.environ["HF_HUB_DISABLE_XET"] = "1"

from huggingface_hub import snapshot_download

IGNORE_PATTERNS = [
    "*.onnx*",
    "*.msgpack*",
    "*.h5*",
    "*.ot",
    "*openvino*",
    "*.tflite*",
    "coreml*",
    "*.bin",  # model.safetensors is preferred
]


def download_model(repo_id: str, desc: str) -> None:
    print(f"\n[Model Download] {desc} ({repo_id}) ...")
    print("  Filtering out redundant ONNX/Flax/TF formats (saving ~8 GB disk)")
    t0 = time.perf_counter()

    for attempt in range(1, 4):
        try:
            snapshot_download(
                repo_id=repo_id,
                ignore_patterns=IGNORE_PATTERNS,
            )
            print(f"  [OK] {repo_id} ready in {time.perf_counter() - t0:.1f}s")
            return
        except Exception as e:
            print(f"  Attempt {attempt} failed: {e}. Retrying in 3s...", file=sys.stderr)
            time.sleep(3)

    print(f"[Error] Failed to download {repo_id} after 3 attempts.", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    print("=" * 60)
    print("  BIS RECOMMENDATION ENGINE: MODEL PRE-DOWNLOADER")
    print("=" * 60)

    # 1. BGE-M3 Embedder
    download_model("BAAI/bge-m3", "BGE-M3 Multilingual Embedder")

    # 2. BGE-Reranker-v2-m3 Cross-Encoder
    download_model("BAAI/bge-reranker-v2-m3", "BGE-Reranker-v2-m3 Cross-Encoder")

    print("\n" + "=" * 60)
    print("  ALL MODELS SUCCESSFULLY DOWNLOADED AND CACHED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
