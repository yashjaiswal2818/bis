"""Measures the 20 complex real-world scenarios listed in README.md.

The README previously asserted these as hand-typed PASS marks with no harness and no
recorded queries. This script pins the exact query text so the table is reproducible.
Writes datasets/complex_scenario_results.json.

Run: python test_complex_scenarios.py
"""
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.retrieval.hybrid_search_orchestrator import HybridSearchOrchestrator

# (id, dimension, query, expected_code) — expected "NONE" means the relevance gate must return 0 hits.
SCENARIOS = [
    ("CPLX-01", "Tender Legalese", "Municipal PHE tender for centrifugally cast ductile iron pressure pipes", "IS 8329"),
    ("CPLX-02", "Tender Legalese", "CPWD tender for structural steel sections joists angles and tees", "IS 2062"),
    ("CPLX-03", "Tender Legalese", "MoRTH highway bridge pre-stressing low relaxation 7-ply strands", "IS 14268"),
    ("CPLX-04", "Multi-Part Series", "Mild steel wrought pipe fittings Part 2 not tubes Part 1", "IS 1239 (Part 2)"),
    ("CPLX-05", "Multi-Part Series", "Lithium secondary cells Part 2 not Nickel Part 1 under MeitY CRS", "IS 16046 (Part 2)"),
    ("CPLX-06", "Multi-Part Series", "Calcined clay Portland pozzolana cement Part 2 not fly ash Part 1", "IS 1489 (Part 2)"),
    ("CPLX-07", "Intent Disambiguation", "Method of test for compressive strength of concrete cubes", "IS 516"),
    ("CPLX-08", "Intent Disambiguation", "Method of test for cement fineness by dry sieving 90 micron", "IS 4031 (Part 1)"),
    ("CPLX-09", "Intent Disambiguation", "Code of practice for design and construction in structural steel", "IS 800"),
    ("CPLX-10", "Intent Disambiguation", "Seismic design criteria and response reduction factor not ductile detailing", "IS 1893"),
    ("CPLX-11", "Mandatory QCO", "DPIIT mandatory quality control order for children toys safety", "IS 9873"),
    ("CPLX-12", "Mandatory QCO", "MoRTH statutory protective helmets for two-wheeler riders", "IS 4151"),
    ("CPLX-13", "Mandatory QCO", "Packaged drinking water mandatory ISI mark certification", "IS 14543"),
    ("CPLX-14", "MEP Engineering", "Three phase outdoor oil-immersed distribution transformers", "IS 1180"),
    ("CPLX-15", "MEP Engineering", "Code of practice for electrical earthing systems and earth electrodes", "IS 3043"),
    ("CPLX-16", "MEP Engineering", "Submersible pumpsets for deep well irrigation and water supply", "IS 8034"),
    ("CPLX-17", "Colloquial & Hinglish", "RCC chhat ke water leakage ko rokne ke liye waterproofing", "IS 2645"),
    ("CPLX-18", "Colloquial & Trade Jargon", "Makaan aur building slab dhalai Fe 500D grade sariya TMT bar", "IS 1786"),
    ("CPLX-19", "Out-of-Domain Gate", "Hyderabadi biryani recipe with basmati rice and saffron", "NONE"),
    ("CPLX-20", "Out-of-Domain Gate", "How do I set up React with Vite and Tailwind CSS", "NONE"),
]


def base_code(code: str) -> str:
    """Reduces 'IS 1489 (Part 2): 1991' to '1489(Part2)' for edition-insensitive comparison."""
    m = re.match(r"\s*IS\s*([0-9]+)\s*(\([^)]*\))?", (code or "").upper())
    return (m.group(1) + (m.group(2) or "").replace(" ", "")) if m else (code or "")


def main() -> None:
    orchestrator = HybridSearchOrchestrator()
    rows = []
    for cid, dimension, query, expected in SCENARIOS:
        hits = orchestrator.search(query, top_k=5)
        top3 = [h.is_code for h in hits[:3]]
        if expected == "NONE":
            hit_at_1 = len(hits) == 0
            hit_at_3 = hit_at_1
        else:
            hit_at_1 = bool(hits) and base_code(top3[0]) == base_code(expected)
            hit_at_3 = any(base_code(c) == base_code(expected) for c in top3)
        rows.append({
            "id": cid,
            "dimension": dimension,
            "query": query,
            "expected": expected,
            "top1": top3[0] if top3 else None,
            "top3": top3,
            "hits_returned": len(hits),
            "confidence": hits[0].confidence if hits else None,
            "hit_at_1": hit_at_1,
            "hit_at_3": hit_at_3,
        })
        print(f"{cid} {'PASS' if hit_at_1 else 'FAIL':<4} expected={expected:<18} got={top3[0] if top3 else None}")

    out_path = BASE_DIR / "datasets" / "complex_scenario_results.json"
    out_path.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")

    retrieval = [r for r in rows if r["expected"] != "NONE"]
    ood = [r for r in rows if r["expected"] == "NONE"]
    print(f"\nRetrieval scenarios  Hit@1 {sum(r['hit_at_1'] for r in retrieval)}/{len(retrieval)}"
          f"   Hit@3 {sum(r['hit_at_3'] for r in retrieval)}/{len(retrieval)}")
    print(f"Out-of-domain gate   rejected {sum(r['hit_at_1'] for r in ood)}/{len(ood)}")
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
