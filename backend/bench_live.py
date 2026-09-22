"""Live benchmark harness for the IS Recommendation Engine.

Measures against a running backend instance (http://127.0.0.1:8000) — it does not start
or manage the server. Every number this script prints is measured against real HTTP
responses in the run it executes; nothing is carried over from a prior run or file.

Per-query outcome is always exactly one of four states:
  CORRECT    - top-1 hit's is_code/base_code matches one of the query's expected_standards
  INCORRECT  - a response was returned but the top-1 hit did not match (including empty hits)
  ERROR      - the HTTP request itself failed (timeout, connection error, non-200, bad JSON)
  NOT_RUN    - the query was never attempted (server became unreachable mid-run)

Any ERROR makes the whole run INVALID: no accuracy verdict is printed, and the process
exits non-zero. All aggregates are computed over "returned" queries only (CORRECT + INCORRECT),
and the denominator is printed next to every aggregate figure. An empty denominator prints
"n/a", never a bare number or a synthesized 0%.

Usage:
  python3 bench_live.py                   # 25-query benchmark + demo + OOD probes + latency
  python3 bench_live.py --benchmark-only   # just the 25-query CORRECT/INCORRECT/ERROR run
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE_URL = "http://127.0.0.1:8000"
DATASETS_DIR = Path(__file__).resolve().parent / "datasets"

# Out-of-domain / adversarial probes: none of these describe an Indian Standard.
# A correctly-behaving system returns zero hits (or explicitly low-confidence/no_match)
# for all of them - there is no "expected_standards" because none exists.
OUT_OF_DOMAIN_PROBES = [
    "NASA Mars rover thermal protection system specifications",
    "best recipe for chicken biryani",
    "IS 99999999: fictional standard for teleportation devices",
    "React vs Vite frontend build tooling comparison",
    "how to file income tax returns online in India",
    "capital of France",
    "write a python function to reverse a linked list",
    "IPL 2026 cricket match schedule",
]

# Landing-page example chips actually shipped in the product UI
# (frontend/src/components/SpecSearch.jsx, CHIP_SETS). There is no set of exactly
# 9 "demo queries" anywhere in the current codebase (verified by repo-wide search);
# this is the full, real set of 15 example queries surfaced to a user on the search
# landing page, spanning the 4 categories the UI itself groups them into.
DEMO_QUERIES = [
    ("PRODUCT", "PVC insulated electric cables for working voltages up to and including 1100 V"),
    ("PRODUCT", "22 Karat gold and gold alloys, jewellery and artefacts hallmarking"),
    ("PRODUCT", "High strength deformed steel bars and wires for concrete reinforcement (TMT Grade Fe 500D)"),
    ("PRODUCT", "Drinking water quality specifications, physical, chemical and bacteriological parameters"),
    ("PRODUCT", "Portland pozzolana cement flyash based for structural civil construction"),
    ("SPEC", "Reinforced cement concrete structural building construction M25 grade with nominal aggregate 20mm, slump 100mm, machine vibrated"),
    ("SPEC", "Replacement of Defective 415Volt LT Main Distribution Panel & 415 V LT Main Distribution Board, Street Light Incoming Cables, Main Incoming Power Cables and circuit Wirings"),
    ("SPEC", "Supply of 22 Karat gold medals for annual merit awards conforming to national hallmarking standards with 6-digit HUID"),
    ("MULTILINGUAL", "पीवीसी इंसुलेटेड बिजली के तार 1100 वोल्ट"),
    ("MULTILINGUAL", "22 कैरेट सोने के आभूषण हॉलमार्किंग"),
    ("MULTILINGUAL", "पीने का साफ पानी गुणवत्ता परीक्षण"),
    ("MULTILINGUAL", "bijli ke taar 1100V building wiring ke liye"),
    ("NATURAL", "Which BIS standard should we follow for fire safety in school and hospital buildings?"),
    ("NATURAL", "What are the official test methods for drinking water physical and chemical parameters?"),
    ("NATURAL", "Which Indian standard is applicable for rooftop solar grid-tied photovoltaic inverters?"),
]

LATENCY_FIXED_QUERY = "High strength deformed steel bars and wires for concrete reinforcement TMT Fe 500D"
LATENCY_RUNS = 20


def check_health() -> None:
    try:
        resp = urllib.request.urlopen(f"{BASE_URL}/health", timeout=5)
        if resp.status != 200:
            print(f"ERROR: /health returned status {resp.status}")
            sys.exit(1)
        body = json.loads(resp.read().decode("utf-8"))
        if not body.get("models_loaded"):
            print(f"ERROR: /health reports models_loaded={body.get('models_loaded')!r}; server not ready.")
            sys.exit(1)
        print(f"[health] OK: {body}")
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: /health check failed: {e}")
        sys.exit(1)


def call_search(query: str, top_k: int = 5, timeout: float = 60.0) -> dict[str, Any]:
    """Raises on any failure; caller is responsible for catching and recording ERROR."""
    req = urllib.request.Request(
        f"{BASE_URL}/search",
        data=json.dumps({"query": query, "top_k": top_k}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.perf_counter()
    resp = urllib.request.urlopen(req, timeout=timeout)
    wall = time.perf_counter() - t0
    if resp.status != 200:
        raise RuntimeError(f"HTTP {resp.status}")
    body = json.loads(resp.read().decode("utf-8"))
    body["_wall_seconds"] = wall
    return body


def server_reachable() -> bool:
    try:
        r = urllib.request.urlopen(f"{BASE_URL}/health", timeout=3)
        return r.status == 200
    except Exception:
        return False


def is_expected_match(hit: dict[str, Any], expected: list[str]) -> bool:
    is_code = hit.get("is_code", "") or ""
    base = is_code.split(":")[0].strip().upper() if is_code else ""
    for exp in expected:
        exp_u = exp.strip().upper()
        if exp_u == is_code.strip().upper():
            return True
        if exp_u == base:
            return True
        if is_code.strip().upper().startswith(exp_u):
            return True
    return False


def load_benchmark_queries() -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    for fname in ("national_evaluation_test_set.json", "public_test_set.json"):
        p = DATASETS_DIR / fname
        if p.exists():
            data = json.loads(p.read_text(encoding="utf-8"))
            for item in data:
                item = dict(item)
                item["_source_file"] = fname
                queries.append(item)
    return queries


def fmt_pct(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{numerator}/{denominator} ({100 * numerator / denominator:.1f}%)"


def run_benchmark(queries: list[dict[str, Any]]) -> dict[str, Any]:
    """Runs the CORRECT/INCORRECT/ERROR/NOT_RUN state machine. Returns a result dict."""
    print("\n" + "=" * 78)
    print(f"BENCHMARK RUN: {len(queries)} queries (national_evaluation_test_set.json + public_test_set.json)")
    print("=" * 78)

    states: list[str] = []
    top1_scores: list[float] = []
    correct_scores: list[float] = []
    per_query_log: list[dict[str, Any]] = []
    aborted = False

    for i, q in enumerate(queries):
        qid = q.get("id", f"Q{i+1}")
        query_text = q["query"]
        expected = q.get("expected_standards", q.get("expected_code", []))

        if aborted:
            states.append("NOT_RUN")
            per_query_log.append({"id": qid, "state": "NOT_RUN", "reason": "server unreachable earlier in run"})
            print(f"  [{qid}] NOT_RUN (server unreachable earlier in run)")
            continue

        try:
            data = call_search(query_text, top_k=5)
        except Exception as e:
            states.append("ERROR")
            per_query_log.append({"id": qid, "state": "ERROR", "error": f"{type(e).__name__}: {e}"})
            print(f"  [{qid}] ERROR: {type(e).__name__}: {e}")
            if not server_reachable():
                print("  [!] Server no longer reachable -- remaining queries will be marked NOT_RUN.")
                aborted = True
            continue

        hits = data.get("hits", [])
        if not hits:
            states.append("INCORRECT")
            per_query_log.append({"id": qid, "state": "INCORRECT", "reason": "zero hits returned", "match_quality": data.get("match_quality")})
            print(f"  [{qid}] INCORRECT (zero hits, match_quality={data.get('match_quality')})")
            continue

        top = hits[0]
        score = float(top.get("rerank_score", 0.0))
        top1_scores.append(score)
        correct = is_expected_match(top, expected)
        state = "CORRECT" if correct else "INCORRECT"
        states.append(state)
        if correct:
            correct_scores.append(score)
        per_query_log.append({
            "id": qid, "state": state, "top1_code": top.get("is_code"),
            "score": round(score, 4), "confidence": top.get("confidence"),
            "expected": expected, "wall_s": round(data.get("_wall_seconds", 0.0), 3),
        })
        print(f"  [{qid}] {state:<9} top1={top.get('is_code'):<22} score={score:.4f} conf={top.get('confidence'):<6} expected={expected}")

    n_correct = states.count("CORRECT")
    n_incorrect = states.count("INCORRECT")
    n_error = states.count("ERROR")
    n_not_run = states.count("NOT_RUN")
    returned = n_correct + n_incorrect  # denominator for accuracy aggregates

    print("\n" + "-" * 78)
    print("STATE COUNTS")
    print("-" * 78)
    print(f"  CORRECT:   {n_correct}")
    print(f"  INCORRECT: {n_incorrect}")
    print(f"  ERROR:     {n_error}")
    print(f"  NOT_RUN:   {n_not_run}")
    print(f"  TOTAL:     {len(queries)}")

    is_invalid = n_error > 0 or returned == 0

    print("\n" + "-" * 78)
    print("AGGREGATES (denominator = CORRECT + INCORRECT = queries that returned a response)")
    print("-" * 78)
    print(f"  Score (top-1 accuracy over returned queries): {fmt_pct(n_correct, returned)}")

    if top1_scores:
        dist = sorted(round(s, 4) for s in top1_scores)
        print(f"  Full top-1 score distribution (n={len(dist)}): {dist}")
    else:
        print("  Full top-1 score distribution: n/a (no queries returned)")

    clamp_count = sum(1 for s in top1_scores if s >= 0.999)
    print(f"  Clamped at 0.999 (n={len(top1_scores)} returned scores): {clamp_count}")

    if correct_scores:
        print(f"  Lowest correct score (n={len(correct_scores)} correct): {min(correct_scores):.4f}")
        below_75 = sum(1 for s in correct_scores if s < 0.75)
        print(f"  Correct answers scoring below 0.75 (of {len(correct_scores)} correct): {below_75}")
    else:
        print("  Lowest correct score: n/a (zero correct)")
        print("  Correct answers scoring below 0.75: n/a (zero correct)")

    print("\n" + "-" * 78)
    if is_invalid:
        if n_error > 0:
            print(f"INVALID RUN: Encountered {n_error} error(s). No accuracy verdict.")
        else:
            print("INVALID RUN: Zero queries returned data. No accuracy verdict.")
    else:
        print(f"VALID RUN: {returned}/{len(queries)} queries returned a response, 0 errors.")
    print("-" * 78)

    return {
        "total": len(queries), "correct": n_correct, "incorrect": n_incorrect,
        "error": n_error, "not_run": n_not_run, "returned": returned,
        "is_invalid": is_invalid, "top1_scores": top1_scores, "correct_scores": correct_scores,
        "per_query_log": per_query_log,
    }


def run_demo_queries() -> None:
    print("\n" + "=" * 78)
    print(f"DEMO QUERIES: {len(DEMO_QUERIES)} (frontend landing-page example chips, all 4 categories)")
    print("=" * 78)
    for category, query_text in DEMO_QUERIES:
        try:
            data = call_search(query_text, top_k=5)
        except Exception as e:
            print(f"  [{category}] ERROR on \"{query_text[:60]}\": {type(e).__name__}: {e}")
            continue
        hits = data.get("hits", [])
        if not hits:
            print(f"  [{category}] \"{query_text[:55]}\" -> NO HITS (match_quality={data.get('match_quality')})")
            continue
        top = hits[0]
        qco_present = bool(top.get("qco_rules"))
        edition_state = (top.get("edition_context") or {}).get("state")
        print(
            f"  [{category:<12}] \"{query_text[:50]:<50}\" -> {top.get('is_code'):<20} "
            f"score={top.get('rerank_score'):.4f} conf={top.get('confidence'):<6} "
            f"match_quality={data.get('match_quality'):<10} qco_present={qco_present!s:<5} edition_state={edition_state}"
        )


def run_ood_probes() -> None:
    print("\n" + "=" * 78)
    print(f"OUT-OF-DOMAIN PROBES: {len(OUT_OF_DOMAIN_PROBES)}")
    print("=" * 78)
    for query_text in OUT_OF_DOMAIN_PROBES:
        try:
            data = call_search(query_text, top_k=5)
        except Exception as e:
            print(f"  ERROR on \"{query_text[:60]}\": {type(e).__name__}: {e}")
            continue
        hits = data.get("hits", [])
        if not hits:
            print(f"  \"{query_text[:55]:<55}\" -> 0 hits (match_quality={data.get('match_quality')}) [correctly rejected]")
        else:
            top = hits[0]
            print(
                f"  \"{query_text[:55]:<55}\" -> {len(hits)} hit(s), top={top.get('is_code')} "
                f"score={top.get('rerank_score'):.4f} conf={top.get('confidence')} "
                f"match_quality={data.get('match_quality')} [FALSE POSITIVE if this looks plausible]"
            )


def run_latency_suite() -> None:
    print("\n" + "=" * 78)
    print(f"LATENCY: 20 consecutive searches, fixed query: \"{LATENCY_FIXED_QUERY}\"")
    print("=" * 78)
    wall_times: list[float] = []
    server_times: list[float] = []
    crashes = 0
    for i in range(1, LATENCY_RUNS + 1):
        try:
            data = call_search(LATENCY_FIXED_QUERY, top_k=5)
            wall = data["_wall_seconds"]
            server_lat = data.get("latency_seconds")
            wall_times.append(wall)
            if server_lat is not None:
                server_times.append(server_lat)
            print(f"  run {i:2d}: wall={wall:.3f}s server_latency={server_lat}")
        except Exception as e:
            crashes += 1
            print(f"  run {i:2d}: CRASH/ERROR: {type(e).__name__}: {e}")
            if not server_reachable():
                print("  [!] Server unreachable; aborting remaining latency runs.")
                break

    print("\n" + "-" * 78)
    if wall_times:
        print(f"  n={len(wall_times)}/{LATENCY_RUNS} completed | crashes/errors: {crashes}")
        print(f"  wall-clock:   min={min(wall_times):.3f}s  median={statistics.median(wall_times):.3f}s  max={max(wall_times):.3f}s")
        if server_times:
            print(f"  server-side:  min={min(server_times):.3f}s  median={statistics.median(server_times):.3f}s  max={max(server_times):.3f}s")
    else:
        print(f"  n=0/{LATENCY_RUNS} completed | crashes/errors: {crashes} -> latency stats: n/a")
    print("-" * 78)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-only", action="store_true", help="Run only the 25-query CORRECT/INCORRECT/ERROR benchmark.")
    args = parser.parse_args()

    check_health()

    queries = load_benchmark_queries()
    if not queries:
        print("ERROR: Zero benchmark queries loaded from backend/datasets/. Cannot run.")
        sys.exit(1)

    result = run_benchmark(queries)

    if not args.benchmark_only:
        run_demo_queries()
        run_ood_probes()
        run_latency_suite()

    if result["is_invalid"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
