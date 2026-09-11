"""Tender Document Parser.

Extracts technical specifications and product line items from digital PDFs
and CSV/Excel Bills of Quantities (BoQs), isolating engineering scope from
administrative, financial, and legal tender boilerplate.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

# Administrative & Commercial Boilerplate Patterns
NON_TECHNICAL_PATTERNS = [
    r"\bearnest money deposit\b",
    r"\bearnest money\b",
    r"\bemd\b",
    r"\barbitration\b",
    r"\bpayment terms\b",
    r"\bsecurity deposit\b",
    r"\bliquidated damages\b",
    r"\bforce majeure\b",
    r"\bgst\b",
    r"\bgstin\b",
    r"\bturnover\b",
    r"\bpan\s*card\b",
    r"\btan\s*card\b",
    r"\baffidavit\b",
    r"\bblacklisted\b",
    r"\bdebarred\b",
    r"\blitigation\b",
    r"\bdigital signature\b",
    r"\bdsc\b",
    r"\bprice bid\b",
    r"\bfinancial bid\b",
    r"\bcorrigendum\b",
    r"\bvalidity period\b",
    r"\benrol(?:ment|lment)\b",
]

# Engineering & Technical Signals (to prevent discarding technical clauses that mention commercial terms)
TECHNICAL_SIGNALS = [
    r"\bpanel\b", r"\bcables?\b", r"\bwiring\b", r"\bfeeder\b", r"\btransformer\b",
    r"\bswitchgear\b", r"\bconduit\b", r"\bsubstation\b", r"\bdistribution board\b",
    r"\blt\b", r"\bht\b", r"\bkv\b", r"\bvolts?\b", r"\bbreaker\b", r"\bmcb\b",
    r"\bmccb\b", r"\bpipe\b", r"\bfittings?\b", r"\bcement\b", r"\bsteel\b",
    r"\breinforcement\b", r"\btmt\b", r"\bconcrete\b", r"\bis\s*:\s*\d+\b",
    r"\bis\s+\d{3,5}\b", r"\bspecification\b", r"\bgrade\b", r"\bdiameter\b",
    r"\bthickness\b", r"\brating\b", r"\bcapacity\b", r"\bsupply of\b",
    r"\binstallation of\b", r"\berection of\b", r"\breplacement of\b",
    r"\blighting\b", r"\bluminaire\b", r"\bsanitary\b", r"\bvalves?\b",
    r"\bpump\b", r"\bmotor\b", r"\bgenerator\b", r"\bapparatus\b",
    r"\bswitch\b", r"\bsocket\b", r"\bearthing\b", r"\binsulat(?:ed|ion)\b",
]


@dataclass
class TenderExtractionResult:
    filename: str
    total_pages_or_rows: int
    technical_clauses: list[str] = field(default_factory=list)
    boq_items: list[dict[str, str]] = field(default_factory=list)
    has_scanned_pages: bool = False
    warning_message: str | None = None


def is_pure_boilerplate(text: str) -> bool:
    """Checks if text contains purely administrative boilerplate with no technical substance."""
    text_lower = text.lower()
    has_non_tech = any(re.search(pat, text_lower) for pat in NON_TECHNICAL_PATTERNS)
    if not has_non_tech:
        return False
    # If it has non-technical keywords, check if it also has strong engineering signals
    has_tech = any(re.search(pat, text_lower) for pat in TECHNICAL_SIGNALS)
    # If it has engineering signals, do not discard as pure boilerplate
    return not has_tech


def decompose_composite_scope(scope_text: str) -> list[str]:
    """Decomposes a multi-item tender title into standalone engineering items."""
    cleaned = " ".join(scope_text.split()).strip()
    if not cleaned:
        return []

    # 1. Remove trailing location/administrative tail
    cleaned = re.sub(
        r"\s+at\s+[A-Z0-9][a-zA-Z0-9\s,]+(?:Club|Factory|Office|Complex|Campus|Station|Building|Hospital|Zone|Area|Division|Badmal|Premises|Site).*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    # 2. Remove common action prefixes
    core = re.sub(
        r"^(?:Replacement of (?:defective )?|Supply of |Installation of |Provision of |Providing and (?:fixing|laying) |Erection of |Work of |Procurement of )\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    ).strip()

    sub_items = []
    # 3. Split on commas or conjunctions separating distinct items
    parts = [p.strip() for p in re.split(r"[,;]|\s+and\s+", core) if len(p.strip()) > 5]
    for part in parts:
        if any(re.search(pat, part.lower()) for pat in TECHNICAL_SIGNALS) or len(part.split()) >= 2:
            sub_items.append(part)

    return sub_items if len(sub_items) > 1 else [cleaned]


def extract_rows_from_nit_grid(text: str) -> list[str]:
    """Extracts line item work descriptions from multi-column NIT summary tables."""
    scopes = []
    header_pattern = r"(?:S\.?N\.?|Sl\.?\s*No\.?|Item\s*No\.?)?[|\s]*(?:Name of Work|Description of Work|Title of Work|Scope of Work|Nomenclature)"
    m_head = re.search(header_pattern, text, re.IGNORECASE)
    if not m_head:
        return scopes

    # Restrict table boundary strictly before subsequent sections (EMD, Eligibility, Notes)
    raw_tail = text[m_head.end():]
    table_content = re.split(
        r"\n\s*(?:Earnest Money|EMD|Eligibility|Evaluation|Terms|Instructions|Note|N\.B|\bGeneral\b)",
        raw_tail,
        flags=re.IGNORECASE,
    )[0]

    # Find rows beginning with item numbers (01, 1, 02, etc.) following the header
    row_pattern = (
        r"(?:^|\n)[|\s]*(?:0?[1-9]|\d{2})[|\s\.\-]+(.*?)"
        r"(?=\s*[|]\s*\d{1,2}[,\d]*/-|\s+\d{1,2}[,\d]*/-|\bEstimated\b|\bEarnest\b|\bEMD\b|\n[|\s]*(?:0?[2-9]|\d{2})[|\s\.\-]|\n\n|\Z)"
    )
    for m in re.finditer(row_pattern, table_content, re.DOTALL | re.IGNORECASE):
        scope = " ".join(m.group(1).replace("|", " ").split()).strip()
        if len(scope) > 12 and not is_pure_boilerplate(scope):
            scopes.append(scope)
    return scopes


def extract_key_value_nit_scope(text: str) -> list[str]:
    """Extracts work scope from key-value formatted NIT notices (e.g., 'Name of Work: ...')."""
    scopes = []
    pattern = (
        r"(?:Name of Work|Description of Work|Title of Work|Scope of Work|Subject)\s*[:\-]\s*(.*?)"
        r"(?=\n\s*(?:Estimated|EMD|Earnest|Time for|Period of|Cost|Eligibility|Turnover|Bid Submission|Date of Opening)|\n\n|\Z)"
    )
    for m in re.finditer(pattern, text, re.DOTALL | re.IGNORECASE):
        scope = " ".join(m.group(1).split()).strip()
        if len(scope) > 12 and not is_pure_boilerplate(scope):
            scopes.append(scope)
    return scopes


class TenderDocumentParser:
    @staticmethod
    def parse_pdf_bytes(pdf_bytes: bytes, filename: str = "tender.pdf") -> TenderExtractionResult:
        """Parses digital PDF tender, isolating technical specifications and work scope."""
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        technical_chunks: list[str] = []
        boq_items: list[dict[str, str]] = []
        scanned_detected = False
        full_document_pages = []

        for page_num in range(total_pages):
            page = doc[page_num]
            raw_text = page.get_text("text")
            text = raw_text.strip() if isinstance(raw_text, str) else ""
            full_document_pages.append(text)

            # Check if page is scanned image (has images but minimal text)
            if len(text) < 40 and len(page.get_images()) > 0:
                scanned_detected = True
                continue

            # 1. PyMuPDF Table Extraction (vector/grid tables)
            if hasattr(page, "find_tables"):
                try:
                    tables = page.find_tables()
                    for tab in tables:
                        table_data = tab.extract()
                        if not table_data or len(table_data) < 2:
                            continue

                        headers = [str(c).strip().lower() if c else "" for c in table_data[0]]
                        desc_col_idx = -1
                        qty_col_idx = -1
                        unit_col_idx = -1

                        for idx, h in enumerate(headers):
                            if any(w in h for w in ["work", "description", "item", "scope", "particular", "nomenclature", "specification"]):
                                if desc_col_idx == -1 or "work" in h or "description" in h:
                                    desc_col_idx = idx
                            if any(q in h for q in ["qty", "quantity"]):
                                qty_col_idx = idx
                            if any(u in h for u in ["unit"]):
                                unit_col_idx = idx

                        if desc_col_idx != -1:
                            for row in table_data[1:]:
                                if desc_col_idx < len(row) and row[desc_col_idx]:
                                    val = " ".join(str(row[desc_col_idx]).split()).strip()
                                    if len(val) > 10 and not is_pure_boilerplate(val):
                                        technical_chunks.append(val)
                                        for d in decompose_composite_scope(val):
                                            if d not in technical_chunks:
                                                technical_chunks.append(d)

                                        qty_val = str(row[qty_col_idx]).strip() if qty_col_idx != -1 and qty_col_idx < len(row) and row[qty_col_idx] else None
                                        unit_val = str(row[unit_col_idx]).strip() if unit_col_idx != -1 and unit_col_idx < len(row) and row[unit_col_idx] else None
                                        if qty_val or unit_val:
                                            boq_items.append({
                                                "description": val,
                                                "quantity": qty_val or "1",
                                                "unit": unit_val or "Nos",
                                            })
                except Exception:
                    pass

        combined_text = "\n\n".join(full_document_pages)

        # 2. Targeted NIT Grid Extraction (for tables rendered as text)
        grid_scopes = extract_rows_from_nit_grid(combined_text)
        for g_scope in grid_scopes:
            if g_scope not in technical_chunks:
                technical_chunks.append(g_scope)
            for d in decompose_composite_scope(g_scope):
                if d not in technical_chunks:
                    technical_chunks.append(d)

        # 3. Targeted NIT Key-Value Extraction ('Name of Work: ...')
        kv_scopes = extract_key_value_nit_scope(combined_text)
        for kv_scope in kv_scopes:
            if kv_scope not in technical_chunks:
                technical_chunks.append(kv_scope)
            for d in decompose_composite_scope(kv_scope):
                if d not in technical_chunks:
                    technical_chunks.append(d)

        # 4. Block-level parsing for full technical specification documents
        for page_num in range(total_pages):
            page = doc[page_num]
            blocks = page.get_text("blocks")
            for block in blocks:
                block_text = block[4].strip() if len(block) > 4 and isinstance(block[4], str) else ""
                if len(block_text) < 35:
                    continue

                if is_pure_boilerplate(block_text):
                    continue

                cleaned_block = " ".join(block_text.split()).strip()
                # Skip the table header/summary block itself to prevent noisy composite tokens
                if re.search(r"Name of Work.*?(?:Estimated|EMD|Earnest)", cleaned_block, re.IGNORECASE):
                    continue

                if any(re.search(pat, cleaned_block.lower()) for pat in TECHNICAL_SIGNALS):
                    technical_chunks.append(cleaned_block)

        # 5. Deduplicate while preserving order
        seen = set()
        deduped_chunks = []
        for chunk in technical_chunks:
            norm = " ".join(chunk.lower().split())
            if norm not in seen and len(chunk) > 10:
                seen.add(norm)
                deduped_chunks.append(chunk)

        warning = None
        if scanned_detected:
            warning = "Notice: Some pages in this tender document appear to be scanned images. Text from digital pages was extracted."
        elif not deduped_chunks and not boq_items:
            warning = "Notice: Could not detect technical specification clauses. The uploaded document may only contain commercial/administrative conditions."

        return TenderExtractionResult(
            filename=filename,
            total_pages_or_rows=total_pages,
            technical_clauses=deduped_chunks[:20],
            boq_items=boq_items[:20],
            has_scanned_pages=scanned_detected,
            warning_message=warning,
        )

    @staticmethod
    def parse_csv_boq(csv_text: str, filename: str = "boq.csv") -> TenderExtractionResult:
        """Parses CSV Bill of Quantities (BoQ) spreadsheet for product line items."""
        reader = csv.DictReader(io.StringIO(csv_text))
        items = []

        desc_key = next((f for f in (reader.fieldnames or []) if "desc" in f.lower() or "item" in f.lower() or "spec" in f.lower() or "work" in f.lower()), None)
        qty_key = next((f for f in (reader.fieldnames or []) if "qty" in f.lower() or "quantity" in f.lower()), None)
        unit_key = next((f for f in (reader.fieldnames or []) if "unit" in f.lower()), None)

        for row in reader:
            desc = row.get(desc_key, "").strip() if desc_key else ""
            if desc and not is_pure_boilerplate(desc):
                items.append({
                    "description": desc,
                    "quantity": row.get(qty_key, "").strip() if qty_key else "1",
                    "unit": row.get(unit_key, "").strip() if unit_key else "Nos",
                })

        return TenderExtractionResult(
            filename=filename,
            total_pages_or_rows=len(items),
            boq_items=items,
        )
