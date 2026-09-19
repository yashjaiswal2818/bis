"""Parser for Scheme-II (CRS - Compulsory Registration Scheme) scraped markdown table.

Extracts all statutory electronics, IT, solar, and LED lighting products governed by MeitY / MNRE / BIS.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CRS_MD_PATH = Path(__file__).resolve().parent.parent / "data" / "scraped_sources" / "crs_portal.md"
OUTPUT_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "scraped_sources" / "bis_scheme2_crs_mandatory.json"


def parse_crs_table():
    if not CRS_MD_PATH.exists():
        print(f"[Error] File not found: {CRS_MD_PATH}")
        return

    content = CRS_MD_PATH.read_text(encoding="utf-8")
    lines = content.splitlines()

    records = []
    seen = set()

    for line in lines:
        if not line.strip().startswith("|") or "---" in line or "Sl. No." in line:
            continue

        parts = [p.strip() for p in line.split("|")]
        # Structure is | [empty] | Sl. No. | Product | IS No. | Date | [empty]
        filtered = [p for p in parts if p]
        if len(filtered) < 4:
            continue

        sl_no = filtered[0]
        product = filtered[1].replace("<br>", " ").strip()
        is_no_raw = filtered[2].replace("\\*", "").replace("*", "").strip()
        impl_date = filtered[3] if len(filtered) > 3 else ""

        # Some lines have multiple standards separated by comma or &
        standards = [s.strip() for s in re.split(r"[,&/]", is_no_raw) if "IS" in s]
        if not standards:
            standards = [is_no_raw]

        ministry = "MeitY (Ministry of Electronics & IT)"
        if any(kw in product.lower() for kw in ["photovoltaic", "solar", "inverter", "storage battery"]):
            ministry = "MNRE (Ministry of New and Renewable Energy)"

        for std in standards:
            # Clean standard text
            std_clean = re.sub(r"\s+", " ", std).strip()
            # Standardize e.g. "IS 13252(Part 1):2010" -> "IS 13252 (Part 1): 2010"
            std_clean = re.sub(r"\(Part", " (Part", std_clean)
            std_clean = re.sub(r":(\d)", r": \1", std_clean)
            std_clean = re.sub(r"\s+", " ", std_clean).strip()

            key = (std_clean.lower().replace(" ", ""), product.lower())
            if key in seen:
                continue
            seen.add(key)

            warning = (
                f"MANDATORY: Under Electronics & IT Goods Compulsory Registration Order (Scheme-II CRS), "
                f"{product} must be registered with BIS conforming to {std_clean} and bear valid R-Number. "
                "Supply or procurement without active BIS CRS registration is prohibited by law."
            )

            records.append({
                "is_code": std_clean,
                "product_category": product,
                "category_group": "Electronics & IT Goods (Compulsory Registration Scheme)",
                "scheme_type": "Scheme-II (Compulsory Registration Scheme - CRS)",
                "is_mandatory": True,
                "issuing_ministry": ministry,
                "order_name": "Electronics & IT Goods (Compulsory Registration) Order",
                "effective_date": impl_date,
                "compliance_warning": warning,
                "source_portal": "https://www.crsbis.in/BIS/products.do",
            })

    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[Success] Extracted {len(records)} statutory Scheme-II CRS products.")
    print(f"[Success] Saved to: {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    parse_crs_table()

