"""Parser for Official BIS Scheme-I Compulsory Certification Table.

Extracts all statutory QCO records from the scraped BIS HTML table:
- IS Number & Revision
- Product Category & Description
- Category Group (Cement, Steel, Electrical, etc.)
- Quality Control Order Name & S.O. Notification Details
- Gazette Notification PDF link
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

CACHE_HTML_PATH = Path("/Users/shraddhajaiswal/.gemini/antigravity/brain/6a239a27-e379-48c7-8f86-ff9b30b91442/.system_generated/steps/249/content.md")
OUTPUT_JSON_PATH = Path(__file__).resolve().parent.parent / "data" / "scraped_sources" / "bis_scheme1_mandatory.json"

# Known Ministry mapping heuristics based on order keywords
MINISTRY_MAPPING = [
    (r"steel", "Ministry of Steel"),
    (r"cement|fastener|footwear|toy|boiler|leather|refrigerator|air conditioner|plywood|wood", "DPIIT (Ministry of Commerce & Industry)"),
    (r"chemical|petro|fertilizer", "Ministry of Chemicals & Petrochemicals"),
    (r"heavy industry|automobile|motor|pump", "Ministry of Heavy Industries"),
    (r"power|transformer|cable|wire", "Ministry of Power / DPIIT"),
    (r"consumer affairs|hallmark|food", "Ministry of Consumer Affairs, Food & Public Distribution"),
    (r"textile|jute", "Ministry of Textiles"),
    (r"health|medical|syringe", "Ministry of Health & Family Welfare"),
    (r"electronics|it|computer", "MeitY (Ministry of Electronics & IT)"),
    (r"road|highway|bitumen", "Ministry of Road Transport and Highways (MoRTH)"),
    (r"petroleum|gas|cylinder|valve", "Ministry of Petroleum & Natural Gas / PESO"),
]


def detect_ministry(order_text: str, product_text: str) -> str:
    combined = f"{order_text} {product_text}".lower()
    for pattern, ministry in MINISTRY_MAPPING:
        if re.search(pattern, combined):
            return ministry
    return "Government of India / Statutory Authority"


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_scheme1_table():
    if not CACHE_HTML_PATH.exists():
        print(f"[Error] Source cache not found at: {CACHE_HTML_PATH}", file=sys.stderr)
        return

    print(f"Reading BIS HTML from {CACHE_HTML_PATH} ...")
    html_content = CACHE_HTML_PATH.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, "html.parser")

    # Find the main table in the desktop view
    table = soup.find("table")
    if not table:
        print("[Error] No table found in HTML source.", file=sys.stderr)
        return

    rows = table.find_all("tr")
    print(f"Found {len(rows)} rows in table. Extracting records...")

    current_category = "General Products"
    current_notification = ""
    current_pdf_link = ""

    extracted_records = []
    seen_standards = set()

    for tr in rows:
        # 1. Check for Category Header (colspan attribute)
        colspan_th = tr.find(["th", "td"], colspan=True)
        if colspan_th:
            header_text = clean_text(colspan_th.get_text())
            # Avoid the table header itself
            if header_text and not header_text.lower().startswith("sr no"):
                current_category = header_text
            continue

        tds = tr.find_all("td")
        if not tds:
            continue

        # Format A: 4 columns -> [Sr No., IS No., Product, Notification]
        # Format B: 3 columns -> [Sr No., IS No., Product] (inherits rowspan notification)
        if len(tds) >= 4:
            is_no_raw = clean_text(tds[1].get_text())
            product_raw = clean_text(tds[2].get_text())
            notif_td = tds[3]
            current_notification = clean_text(notif_td.get_text(separator=" "))
            link_tag = notif_td.find("a")
            current_pdf_link = link_tag["href"].strip() if link_tag and link_tag.has_attr("href") else ""
        elif len(tds) == 3:
            is_no_raw = clean_text(tds[1].get_text())
            product_raw = clean_text(tds[2].get_text())
        else:
            continue

        # Clean IS number
        # Example formats: "IS 12330", "IS 1489 (Part 1)", "IS/IEC 60898", "IS 1786: 2008"
        if not is_no_raw or is_no_raw == "-" or len(is_no_raw) < 3:
            continue

        # Match IS code pattern
        is_match = re.search(r"\bIS(?:\s*[:/\-–]?\s*|\s+)(?:IEC\s*)?[\d\w\(\)\s:/\-]+", is_no_raw, re.IGNORECASE)
        is_code = is_match.group(0).strip() if is_match else is_no_raw
        is_code = re.sub(r"\s+", " ", is_code).replace(" :", ":")

        # Extract Quality Control Order name
        order_match = re.search(r"([^,\n\.]+(?:Quality Control|QCO|Order)[^,\n\.]*)", current_notification, re.IGNORECASE)
        order_name = order_match.group(0).strip() if order_match else (current_notification[:80] if current_notification else f"{current_category} Quality Control Mandate")
        order_name = re.sub(r"^\d+\.\s*", "", order_name)

        # Extract S.O. Notification number and Date
        so_match = re.search(r"(?:S\.O\.?\s*(?:No\.?\s*)?[\d\w\(\)]+(?:\s*[–\-]\s*\w+)?(?:\s*Dated?\s*[\d\w\s,]+)?)", current_notification, re.IGNORECASE)
        so_details = so_match.group(0).strip() if so_match else ""

        # Extract effective/notification date if present
        date_match = re.search(r"\b(?:\d{1,2}[\s/\-](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|[A-Za-z]+|\d{1,2})[\s/\-]\d{2,4}|\d{4}-\d{2}-\d{2})\b", current_notification, re.IGNORECASE)
        effective_date = date_match.group(0).strip() if date_match else None

        ministry = detect_ministry(order_name, product_raw)

        # Compliance warning following Build Philosophy
        warning = (
            f"MANDATORY: Under {order_name} ({so_details or 'Statutory Gazette Order'}), "
            f"{product_raw} must carry the BIS Standard Mark (ISI Mark) conforming to {is_code}. "
            "Supplies, manufacturing, or procurement without valid BIS CML license is prohibited by law."
        )

        record = {
            "is_code": is_code,
            "product_category": product_raw,
            "category_group": current_category,
            "scheme_type": "Scheme-I (Mandatory ISI Mark)",
            "is_mandatory": True,
            "issuing_ministry": ministry,
            "order_name": order_name,
            "so_notification": so_details,
            "effective_date": effective_date,
            "gazette_pdf_url": current_pdf_link,
            "compliance_warning": warning,
            "source_portal": "https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-i-mark-scheme/",
        }

        # Deduplicate on normalized IS code
        norm_key = re.sub(r"[^a-z0-9]", "", is_code.lower())
        if norm_key not in seen_standards:
            seen_standards.add(norm_key)
            extracted_records.append(record)

    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON_PATH.write_text(json.dumps(extracted_records, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[Success] Extracted {len(extracted_records)} unique statutory mandatory standards.")
    print(f"[Success] Saved to: {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    parse_scheme1_table()

