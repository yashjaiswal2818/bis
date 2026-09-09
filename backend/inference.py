"""MANDATORY Hackathon Judge Entry Point.

Usage:
    python inference.py --input <input_json_path> --output <output_json_path>

Executes 100% offline hybrid retrieval against precomputed indexes,
reporting exact retrieved standards and per-query latency.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add backend directory to sys.path so imports resolve cleanly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.retrieval.hybrid_search_orchestrator import HybridSearchOrchestrator


def run_inference(input_path: Path, output_path: Path, top_k: int = 5):
    """Runs batch inference over evaluation queries and writes results."""
    if not input_path.exists():
        print(f"[Error] Input dataset not found at: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[Inference] Loading input dataset from {input_path} ...")
    queries = json.loads(input_path.read_text(encoding="utf-8"))
    print(f"[Inference] Total queries to evaluate: {len(queries)}")

    print("[Inference] Initializing Hybrid Search Orchestrator ...")
    orchestrator = HybridSearchOrchestrator(final_k=top_k)
    print("[Inference] Warming up engine models ...")
    orchestrator.search("portland cement specification", top_k=1)
    print("[Inference] Engine ready. Processing queries ...")

    results = []
    total_time = 0.0

    for idx, item in enumerate(queries, start=1):
        q_id = item.get("id", f"Q-{idx:03d}")
        query = item.get("query", "").strip()

        t0 = time.perf_counter()
        recs = orchestrator.search(query, top_k=top_k)
        latency = time.perf_counter() - t0
        total_time += latency

        retrieved_codes = [r.is_code for r in recs]

        out_item = {
            "id": q_id,
            "query": query,
            "retrieved_standards": retrieved_codes,
            "latency_seconds": round(latency, 4),
        }
        if "expected_standards" in item:
            out_item["expected_standards"] = item["expected_standards"]

        results.append(out_item)
        print(f"  [{idx}/{len(queries)}] {q_id}: {len(retrieved_codes)} standards in {latency:.2f}s")

    avg_latency = total_time / max(len(queries), 1)
    print(f"[Inference] Complete! Average latency: {avg_latency:.3f}s per query")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[Inference] Results saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="BIS Recommendation Engine: Inference Entry Point")
    parser.add_argument("--input", "-i", type=str, required=True, help="Path to input queries JSON")
    parser.add_argument("--output", "-o", type=str, required=True, help="Path to output results JSON")
    parser.add_argument("--top_k", "-k", type=int, default=5, help="Number of top standards to retrieve (default: 5)")

    args = parser.parse_args()
    run_inference(Path(args.input), Path(args.output), top_k=args.top_k)


if __name__ == "__main__":
    main()
