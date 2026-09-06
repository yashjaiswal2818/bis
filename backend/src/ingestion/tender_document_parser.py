"""Tender Document Parser.

Extracts technical specifications and product line items from digital PDFs
and CSV/Excel Bills of Quantities (BoQs), filtering out legal boilerplate.
"""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field

# Keywords indicating commercial / non-technical sections to ignore
NON_TECHNICAL_PATTERNS = [
    r"\bearnest money deposit\b",
    r"\bemd\b",
    r"\barbitration\b",
    r"\bpayment terms\b",
    r"\bsecurity deposit\b",
    r"\bliquidated damages\b",
    r"\bforce majeure\b",
    r"\bgst\b",
    r"\bturnover\b",
]

# Keywords indicating technical specifications
TECHNICAL_SECTION_PATTERNS = [
    r"technical specification",
    r"scope of work",
    r"schedule of requirements",
    r"material specifications",
    r"product details",
    r"bill of quantities",
    r"boq",
]


@dataclass
class TenderExtractionResult:
    filename: str
    total_pages_or_rows: int
    technical_clauses: list[str] = field(default_factory=list)
    boq_items: list[dict[str, str]] = field(default_factory=list)
    has_scanned_pages: bool = False
    warning_message: str | None = None


class TenderDocumentParser:
    @staticmethod
    def parse_pdf_bytes(pdf_bytes: bytes, filename: str = "tender.pdf") -> TenderExtractionResult:
        """Parses digital PDF tender, isolating technical specifications."""
        import fitz  # PyMuPDF

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        technical_chunks = []
        scanned_detected = False

        for page_num in range(total_pages):
            page = doc[page_num]
            raw_text = page.get_text("text")
            text = raw_text.strip() if isinstance(raw_text, str) else ""

            # Check if page is scanned image (has images but minimal text)
            if len(text) < 40 and len(page.get_images()) > 0:
                scanned_detected = True
                continue

            # Split page text into paragraphs/clauses
            paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]

            for para in paragraphs:
                para_lower = para.lower()
                # Skip legal boilerplate
                if any(re.search(pat, para_lower) for pat in NON_TECHNICAL_PATTERNS):
                    continue
                # Keep technical requirement paragraphs
                if len(para) > 50:
                    technical_chunks.append(para)

        warning = None
        if scanned_detected:
            warning = "Notice: Some pages in this tender document appear to be scanned images. Text from digital pages was extracted."

        return TenderExtractionResult(
            filename=filename,
            total_pages_or_rows=total_pages,
            technical_clauses=technical_chunks[:20],  # Return top technical clauses
            has_scanned_pages=scanned_detected,
            warning_message=warning,
        )

    @staticmethod
    def parse_csv_boq(csv_text: str, filename: str = "boq.csv") -> TenderExtractionResult:
        """Parses CSV Bill of Quantities (BoQ) spreadsheet for product line items."""
        reader = csv.DictReader(io.StringIO(csv_text))
        items = []

        desc_key = next((f for f in (reader.fieldnames or []) if "desc" in f.lower() or "item" in f.lower() or "spec" in f.lower()), None)
        qty_key = next((f for f in (reader.fieldnames or []) if "qty" in f.lower() or "quantity" in f.lower()), None)
        unit_key = next((f for f in (reader.fieldnames or []) if "unit" in f.lower()), None)

        for row in reader:
            desc = row.get(desc_key, "").strip() if desc_key else ""
            if desc:
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
