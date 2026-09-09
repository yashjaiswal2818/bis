"""Test behavior of search orchestrator on wrong, invalid, or gibberish queries."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.retrieval.hybrid_search_orchestrator import HybridSearchOrchestrator

def main():
    o = HybridSearchOrchestrator()
    wrong_queries = [
        "random gibberish qwertyuiop",
        "buy a margherita pizza with extra cheese",
        "IS 99999999 invalid standard number",
        "how to bake a chocolate cake at home"
    ]
    for q in wrong_queries:
        hits = o.search(q, top_k=3)
        print(f"\nQUERY: \"{q}\"")
        print(f"Returned hits count: {len(hits)}")
        for h in hits:
            print(f"   #{h.rank} {h.is_code:<22} | Score: {h.rerank_score:.3f} | Conf: {h.confidence} | {h.title[:35]}")

if __name__ == "__main__":
    main()
