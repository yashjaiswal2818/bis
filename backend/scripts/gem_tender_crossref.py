"""BUILD-TIME UTILITY -- NOT part of the offline recommendation engine.

Requires network access and a paid third-party API key (Apify) to produce its input;
does not run offline and must not be imported or invoked by the FastAPI app, start.py,
or any other runtime path. The engine's offline-operation claim covers /search,
/tender-audit, /gem-clause, and the rest of src/api and src/retrieval -- it does not
cover this script. Run it manually, by hand, when you have GeM tender export data.

Cross-references real GeM tender listings against the recommendation engine.

Takes a CSV or JSON export of GeM tender records (e.g. from an Apify GeM tender
scraper -- https://apify.com, paid per result, requires an Apify API token) and,
for each one, asks the live /search endpoint what IS code(s) it would recommend
for that tender's title. Flags tenders that don't cite any IS code themselves but
get a HIGH-confidence recommendation -- that's the "this tender should probably
cite a standard and doesn't" case.

This is NOT a GeM API integration. It works from a third-party export of public
tender listings; it does not talk to gem.gov.in in any way. Label any output
from this script accordingly.

Usage (from backend/, with the FastAPI server already running on :8000):
  python3 scripts/gem_tender_crossref.py tenders.csv
  python3 scripts/gem_tender_crossref.py tenders.json --title-field title --limit 50
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE_URL = "http://127.0.0.1:8000"

# Same pattern shape used by AdaptiveQueryPreprocessor.extract_direct_is_codes
# (query_preprocessor.py) -- reused here so "does this text already cite a code"
# is judged the same way the live system itself judges direct-code mentions.
IS_CODE_PATTERN = re.compile(r"\b(?:is|IS)[\s:]*([0-9]+(?:\s*(?:\([^\)]+\)|part\s*[0-9]+))?)\b", re.IGNORECASE)

FIELD_ALIASES = {
    "title": ["title", "Title", "tender_title", "description"],
    "ref": ["tender_ref_no", "tender_id", "ref_no", "id", "bid_no"],
    "org": ["organisation", "organization", "department", "buyer"],
    "closing_date": ["closing_date", "bid_end_date", "deadline"],
    "url": ["detail_url", "url", "link"],
}


def check_health() -> None:
    try:
        resp = urllib.request.urlopen(f"{BASE_URL}/health", timeout=5)
        body = json.loads(resp.read().decode("utf-8"))
        if resp.status != 200 or not body.get("models_loaded"):
            print(f"ERROR: backend not healthy: {body}")
            sys.exit(1)
        print(f"[health] OK: {body}")
    except Exception as e:
        print(f"ERROR: could not reach backend at {BASE_URL}: {e}")
        sys.exit(1)


def resolve_field(row: dict[str, Any], kind: str, override: str | None) -> str:
    if override:
        return str(row.get(override, "") or "")
    for name in FIELD_ALIASES[kind]:
        if name in row and row[name]:
            return str(row[name])
    return ""


def load_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("items") or data.get("results") or list(data.values())
        return list(data)
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def already_cites_is_code(text: str) -> list[str]:
    return [f"IS {m.group(1)}".strip() for m in IS_CODE_PATTERN.finditer(text)]


def call_search(query: str, top_k: int = 3, timeout: float = 60.0) -> dict[str, Any] | None:
    req = urllib.request.Request(
        f"{BASE_URL}/search",
        data=json.dumps({"query": query, "top_k": top_k}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        if resp.status != 200:
            return None
        return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"    [error] {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--title-field", default=None, help="Override the column/key holding the tender text to search on")
    parser.add_argument("--ref-field", default=None)
    parser.add_argument("--org-field", default=None)
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N records (useful for a cheap test pass)")
    parser.add_argument("--out", default="gem_crossref_results.csv")
    args = parser.parse_args()

    if not args.input_file.exists():
        print(f"ERROR: {args.input_file} not found")
        sys.exit(1)

    check_health()

    records = load_records(args.input_file)
    if args.limit:
        records = records[: args.limit]
    if not records:
        print("ERROR: zero records loaded from input file.")
        sys.exit(1)

    print(f"\nProcessing {len(records)} tender record(s) from {args.input_file.name}\n")

    results = []
    already_cited = 0
    high_conf_gap = 0  # doesn't cite a code, system finds a HIGH match -> the actionable case
    no_match = 0
    errors = 0

    for i, row in enumerate(records, start=1):
        title = resolve_field(row, "title", args.title_field)
        ref = resolve_field(row, "ref", args.ref_field) or f"ROW-{i}"
        org = resolve_field(row, "org", args.org_field)

        if not title.strip():
            print(f"  [{ref}] SKIP (empty title field)")
            continue

        cited = already_cites_is_code(title)
        data = call_search(title, top_k=3)

        if data is None:
            errors += 1
            results.append({"ref": ref, "org": org, "title": title, "already_cites": ";".join(cited),
                             "top_recommendation": "ERROR", "confidence": "", "match_quality": "", "gap_flag": ""})
            print(f"  [{ref}] ERROR calling /search")
            continue

        hits = data.get("hits", [])
        match_quality = data.get("match_quality")
        if not hits:
            no_match += 1
            top_code, conf = "", ""
        else:
            top = hits[0]
            top_code, conf = top.get("is_code", ""), top.get("confidence", "")

        gap = ""
        if cited:
            already_cited += 1
        elif hits and conf == "HIGH":
            high_conf_gap += 1
            gap = "GAP: no IS code cited, HIGH-confidence match found"

        results.append({
            "ref": ref, "org": org, "title": title,
            "already_cites": ";".join(cited), "top_recommendation": top_code,
            "confidence": conf, "match_quality": match_quality, "gap_flag": gap,
        })
        flag = f" <-- {gap}" if gap else ""
        cited_display = ";".join(cited) if cited else "none"
        print(f"  [{ref}] cites={cited_display:<20} -> {top_code or '(no hit)':<20} conf={conf}{flag}")

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ref", "org", "title", "already_cites", "top_recommendation", "confidence", "match_quality", "gap_flag"])
        writer.writeheader()
        writer.writerows(results)

    print("\n" + "-" * 78)
    print(f"Processed: {len(results)} | Errors: {errors}")
    print(f"Already cite an IS code in the title: {already_cited}")
    print(f"No code cited, system found a HIGH-confidence match (the actionable gap): {high_conf_gap}")
    print(f"No hits at all (system found nothing relevant): {no_match}")
    print(f"Full results written to: {args.out}")
    print("-" * 78)


if __name__ == "__main__":
    main()
