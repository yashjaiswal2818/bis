"""National Indian Standards Harvester & Database Scaler.

Streams the complete official corpus of 21,300+ Indian Standards from the
public safety open repository (archive.org gov.in.is) across partitioned date ranges,
enriches metadata, seeds SQLite, and updates the lexical BM25 index and anti-hallucination whitelist.
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"

sys.path.insert(0, str(BASE_DIR))

from src.database.sqlite_manager import (
    get_all_standards_for_indexing,
    seed_database_from_files,
)
from src.retrieval.bm25_lexical_indexer import build_bm25_index

DIVISION_KEYWORDS = {
    "Civil Engineering (CED)": r"\b(cement|concrete|aggregates?|brick|blocks?|mortar|pipes?|plywood|timber|masonry|soil|foundation|asphalt|bitumen|roofing|tiles?|doors?|windows?|earthquake|seismic|plumbing|sanitary)\b",
    "Metallurgical Engineering (MTD)": r"\b(steel|iron|alloy|rebar|tmt|gold|silver|hallmark|welding|castings?|wrought|aluminium|copper|brass|wire\s*mesh|zinc|lead|foundry|ferro)\b",
    "Electronics and IT (LITD / CRS)": r"\b(electronics?|computer|battery|batteries|lithium|cell|software|telecom|smart|led|microprocessor|inverter|photovoltaic|solar|audio|video|display)\b",
    "Electrotechnical (ETD)": r"\b(cables?|wires?|transformers?|switchgear|insulators?|generators?|motors?|electrical|voltage|relay|luminaire|substation|high\s*voltage|earthing)\b",
    "Mechanical Engineering (MED)": r"\b(boiler|valves?|pumps?|compressors?|bearings?|gears?|cranes?|hoists?|pressure\s*vessels?|turbines?|cylinders?|automotive|conveyor|tools?|dies)\b",
    "Chemical (CHD)": r"\b(chemical|paint|varnish|acids?|fertilizers?|polymers?|plastics?|adhesives?|rubber|dyes?|cosmetics?|soaps?|detergents?|solvents?|resins?)\b",
    "Food and Agriculture (FAD)": r"\b(drinking\s*water|food|grain|tea|coffee|milk|dairy|spices?|pesticides?|sugar|oilseeds?|flour|bakery|cereal|meat|beverages?|packaging)\b",
    "Textiles (TXD)": r"\b(cotton|yarn|fabric|cloth|silk|jute|wool|fibres?|geotextiles?|garments?|tarpaulin|weaving|spinning|threads?)\b",
    "Transport Engineering (TED)": r"\b(railways?|locomotive|aircraft|marine|ships?|vehicles?|tyres?|brakes?|road\s*vehicles?|suspension)\b",
    "Medical Equipment (MHD)": r"\b(medical|surgical|implants?|hospital|syringes?|orthopaedic|diagnostic|gloves?|catheter|dental)\b"
}


def infer_division(text: str) -> str:
    text_l = text.lower()
    for div, pat in DIVISION_KEYWORDS.items():
        if re.search(pat, text_l):
            return div
    return "General Engineering & Technology"


def extract_clean_is_code(identifier: str, title: str, date: str | None = None) -> tuple[str, str, int | None]:
    """Extracts canonical IS code, clean title, and publication year."""
    # Pattern 1: From Title
    m = re.match(
        r"^\s*([A-Z]+(?:/[A-Z]+)?\s+[\d\.\-]+(?:\s*(?:\([^\)]+\)|Part\s*[\dIVX]+))?)\s*(?::\s*(\d{4}))?",
        title,
        re.IGNORECASE
    )
    year = None
    if m:
        base = m.group(1).strip()
        # Clean hyphenated parts like 'IS 3452-2' -> 'IS 3452 (Part 2)'
        part_hyphen = re.search(r"\b(IS\s+\d+)-(\d+)\b", base, re.IGNORECASE)
        if part_hyphen:
            base = f"{part_hyphen.group(1)} (Part {part_hyphen.group(2)})"

        if m.group(2):
            year = int(m.group(2))
            is_code = f"{base}: {year}"
        elif date and date.isdigit() and len(date) == 4:
            year = int(date)
            is_code = f"{base}: {year}"
        else:
            is_code = base
    else:
        # Fallback to identifier: gov.in.is.3452.2.1970
        parts = identifier.replace("gov.in.is.", "").split(".")
        if len(parts) >= 2 and parts[-1].isdigit() and len(parts[-1]) == 4:
            year = int(parts[-1])
            is_num = " ".join(parts[:-1]).upper()
            is_code = f"IS {is_num}: {year}"
        else:
            is_code = f"IS {identifier.replace('gov.in.is.', '').upper()}"

    # Clean title
    clean_title = re.sub(r"^[A-Z/]+\s+[\d\.\-]+(?:\s*[:-]\s*Part\s*[\dIVX]+)?\s*[:-]\s*", "", title, flags=re.IGNORECASE).strip()
    clean_title = re.sub(r"\(Bi-Lingual\)", "", clean_title, flags=re.IGNORECASE).strip()
    clean_title = re.sub(r"\[.*?\]", "", clean_title).strip()
    if not clean_title:
        clean_title = f"Specification for {is_code}"

    return is_code, clean_title, year


PARTITIONED_QUERIES = [
    "collection:publicsafetycode AND gov.in.is AND year:[* TO 1970]",
    "collection:publicsafetycode AND gov.in.is AND year:[1971 TO 1985]",
    "collection:publicsafetycode AND gov.in.is AND year:[1986 TO 1995]",
    "collection:publicsafetycode AND gov.in.is AND year:[1996 TO 2005]",
    "collection:publicsafetycode AND gov.in.is AND year:[2006 TO 2030]",
    "collection:publicsafetycode AND gov.in.is AND -year:[* TO *]",
]


def get_robust_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BIS-Recommendation-Engine/2.0"})
    return session


def harvest_all_partitions() -> list[dict]:
    print("=" * 70)
    print("  HARVESTING FULL NATIONAL INDIAN STANDARDS CORPUS (~21,304 RECORDS)")
    print("=" * 70)

    raw_cache_file = DATA_DIR / "raw_archive_docs.json"
    unique_docs: dict[str, dict] = {}

    if raw_cache_file.exists():
        try:
            cached_list = json.loads(raw_cache_file.read_text(encoding="utf-8"))
            for d in cached_list:
                if d.get("identifier"):
                    unique_docs[d["identifier"]] = d
            print(f"[*] Loaded {len(unique_docs)} cached archive documents from {raw_cache_file.name}")
        except Exception as e:
            print(f"[!] Warning reading cache: {e}")

    session = get_robust_session()
    rows_per_page = 1000

    for q_idx, q_str in enumerate(PARTITIONED_QUERIES, start=1):
        page = 1
        print(f"\n[*] [Partition {q_idx}/{len(PARTITIONED_QUERIES)}] Query: {q_str}")
        while True:
            params = {
                "q": q_str,
                "fl[]": ["identifier", "title", "date"],
                "rows": rows_per_page,
                "page": page,
                "output": "json"
            }
            t0 = time.perf_counter()
            try:
                resp = session.get("https://archive.org/advancedsearch.php", params=params, timeout=30)
                if resp.status_code != 200:
                    print(f"    [!] HTTP {resp.status_code} on page {page}. Retrying...")
                    time.sleep(2)
                    continue

                data = resp.json()
                docs = data.get("response", {}).get("docs", [])
                if not docs:
                    break

                for d in docs:
                    ident = d.get("identifier")
                    if ident:
                        unique_docs[ident] = d

                print(f"    Page {page}: Fetched {len(docs)} records ({time.perf_counter() - t0:.2f}s) | Total unique: {len(unique_docs)}")
                if len(docs) < rows_per_page:
                    break
                page += 1
                time.sleep(0.2)
            except Exception as e:
                print(f"    [!] Error on partition {q_idx} page {page}: {e}. Retrying after 2s...")
                time.sleep(2)
                # Try once more for this page
                try:
                    resp = session.get("https://archive.org/advancedsearch.php", params=params, timeout=30)
                    data = resp.json()
                    docs = data.get("response", {}).get("docs", [])
                    if docs:
                        for d in docs:
                            if d.get("identifier"):
                                unique_docs[d["identifier"]] = d
                        print(f"    Page {page} (Retry OK): Fetched {len(docs)} records | Total unique: {len(unique_docs)}")
                        if len(docs) < rows_per_page:
                            break
                        page += 1
                        continue
                except Exception:
                    pass
                break

    all_docs = list(unique_docs.values())
    print(f"\n[+] Total unique documents downloaded: {len(all_docs)}")
    raw_cache_file.write_text(json.dumps(all_docs), encoding="utf-8")
    print(f"[+] Cached raw documents to {raw_cache_file.name}")
    return all_docs


def process_and_merge(raw_docs: list[dict]):
    print("\n" + "=" * 70)
    print("  PROCESSING & MERGING CORPUS INTO PARSED STANDARDS")
    print("=" * 70)
    parsed_path = DATA_DIR / "parsed_standards.json"

    existing_st = []
    if parsed_path.exists():
        try:
            existing_st = json.loads(parsed_path.read_text(encoding="utf-8"))
        except Exception:
            existing_st = []

    # Map existing by normalized code to preserve our curated detailed scopes
    existing_map = {}
    for s in existing_st:
        norm = re.sub(r"\s+", "", s["is_code"]).lower()
        existing_map[norm] = s

    print(f"[*] Preserving existing {len(existing_map)} hand-curated detailed standards.")

    # We map by normalized code to guarantee UNIQUE keys for SQLite
    records_by_norm: dict[str, dict] = dict(existing_map)
    added_new = 0

    for doc in raw_docs:
        ident = doc.get("identifier", "")
        raw_title = doc.get("title", "")
        if not raw_title:
            continue

        raw_date = str(doc.get("date", ""))[:4]
        is_code, clean_title, year = extract_clean_is_code(ident, raw_title, raw_date)
        norm_code = re.sub(r"\s+", "", is_code).lower()

        if norm_code in records_by_norm:
            continue

        division = infer_division(clean_title)
        scope_text = (
            f"Indian Standard specification {is_code} covering requirements, dimensions, "
            f"technical properties, sampling, and quality criteria for {clean_title} under {division}."
        )

        record = {
            "is_code": is_code,
            "is_code_norm": norm_code,
            "title": clean_title.upper(),
            "revision": f"Edition {year}" if year else "Latest Published Version",
            "page_start": 1,
            "page_end": 10,
            "scope": scope_text,
            "full_text": f"{is_code}: {clean_title.upper()}. {scope_text}",
            "division": division,
            "status": "ACTIVE",
            "reaffirmation_year": year,
            "amendments_count": 0
        }
        records_by_norm[norm_code] = record
        added_new += 1

    final_records = list(records_by_norm.values())
    print(f"[+] Total merged national corpus: {len(final_records)} standards (+{added_new} newly integrated)!")
    parsed_path.write_text(json.dumps(final_records, indent=2), encoding="utf-8")

    # Update anti-hallucination whitelist
    wl_path = DATA_DIR / "is_code_whitelist.json"
    wl_data = {"canonical": [], "normalized": []}
    canon_set = set()
    norm_set = set()
    for s in final_records:
        canon_set.add(s["is_code"])
        norm_set.add(re.sub(r"\s+", "", s["is_code"]).lower())
    wl_data["canonical"] = sorted(list(canon_set))
    wl_data["normalized"] = sorted(list(norm_set))
    wl_path.write_text(json.dumps(wl_data, indent=2), encoding="utf-8")
    print(f"[+] Anti-hallucination whitelist updated: {len(wl_data['canonical'])} standards whitelisted!")

    return len(final_records)


def seed_and_rebuild_indexes():
    print("\n" + "=" * 70)
    print("  SEEDING SQLITE MASTER DATABASE & REBUILDING BM25 INDEX")
    print("=" * 70)

    standards_json = DATA_DIR / "parsed_standards.json"
    qco_json = DATA_DIR / "qco_mandatory_catalog.json"
    xrefs_json = DATA_DIR / "raw_xrefs.json"
    index_dir = DATA_DIR / "index"
    db_path = DATA_DIR / "standards_master.db"

    # 1. Seed SQLite
    t0 = time.perf_counter()
    counts = seed_database_from_files(
        standards_json=standards_json,
        qco_json=qco_json,
        xrefs_json=xrefs_json,
        db_path=db_path,
    )
    print(f"[+] SQLite database seeded: {counts['standards']} standards, {counts['qco_rules']} QCO rules, {counts['allied_edges']} allied edges in {time.perf_counter() - t0:.2f}s")

    # 2. Rebuild BM25 Lexical Index across all standards
    t0 = time.perf_counter()
    standards = get_all_standards_for_indexing(db_path)
    bm25_path = index_dir / "bm25_index.pkl"
    print(f"[*] Building BM25 index across {len(standards)} standards ...")
    build_bm25_index(standards, output_path=bm25_path)
    print(f"[+] BM25 index built and saved in {time.perf_counter() - t0:.2f}s!")


if __name__ == "__main__":
    raw_docs = harvest_all_partitions()
    total = process_and_merge(raw_docs)
    seed_and_rebuild_indexes()
    print("\n" + "=" * 70)
    print(f"  NATIONAL CORPUS COMPLETE: {total} INDIAN STANDARDS READY!")
    print("=" * 70)
