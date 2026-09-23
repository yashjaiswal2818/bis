"""Regression tests for TenderDocumentParser scoring/selection bugs found against real
tender documents this session.

Each case here is a real bug that was found by uploading an actual document and getting
a wrong audit result, not a hypothetical. That's the point of this file: every future
"is this true?" discovery gets added here as a permanent case, so a future change can't
silently reintroduce it. Run directly (`python3 test_tender_parser_regression.py`) or via
pytest; both work since cases are plain `test_*` functions with asserts.
"""
from __future__ import annotations

import fitz

from src.ingestion.tender_document_parser import (
    TenderDocumentParser,
    is_pure_boilerplate,
    technical_relevance_score,
)


# ---------------------------------------------------------------------------------
# Case 1 (Census/RGI kit-packaging corrigendum): a schedule-revision table with a
# "Particulars | Existing | Revised" header got misread as a technical description
# column because "particular" matched the desc-column header-detection list. Bare
# date-table labels ("Bid Submission Closing", "Technical Bid Opening") were then fed
# into retrieval as if they were engineering clauses, producing nonsense matches
# (a bid-opening date matched a prosthetic-limb "opening" device on keyword overlap).
# ---------------------------------------------------------------------------------
def test_schedule_table_not_read_as_technical_clauses():
    doc = fitz.open()
    page = doc.new_page()
    table_text = (
        "Particulars                Existing              Revised\n"
        "Bid Submission Closing      18-09-2026, 02:00 PM  22-09-2026, 02:00 PM\n"
        "Sample Submission Closing   18-09-2026, 02:00 PM  22-09-2026, 02:00 PM\n"
        "Technical Bid Opening       19-09-2026, 02:00 PM  23-09-2026, 02:00 PM"
    )
    page.insert_textbox(fitz.Rect(50, 50, 550, 250), table_text, fontsize=11)
    for y in (70, 100, 130, 160, 190):
        page.draw_line((50, y), (550, y))
    for x in (50, 250, 400, 550):
        page.draw_line((x, 70), (x, 190))

    result = TenderDocumentParser.parse_pdf_bytes(doc.tobytes(), filename="corrigendum_schedule.pdf")

    assert result.technical_clauses == [], (
        f"Schedule-table date labels leaked into technical_clauses: {result.technical_clauses}"
    )
    assert result.boq_items == [], f"Schedule-table date labels leaked into boq_items: {result.boq_items}"
    assert result.warning_message, "A document with no genuine content must say so, not stay silent."


# ---------------------------------------------------------------------------------
# Case 2 (RCF DAP ET 7 Gantry NIT): joint-venture pre-qualification eligibility bullets
# ("particular construction experience", "financial capability", "cash flow") scored
# the same (0) as genuine technical content and were selected ahead of real fabrication/
# welding specification clauses on document-order tie-breaking.
# ---------------------------------------------------------------------------------
def test_jv_prequalification_bullets_score_negative():
    jv_clauses = [
        "Qualifying factors to be met collectively: (i) particular construction experience and "
        "key production rates; (ii) construction cash flow for the subject contract; "
        "(iii) personnel capabilities; and (iv) equipment capabilities;",
        "Qualifying factors for lead partner: (i) particular construction experience; "
        "(ii) financial capability to meet cash flow requirement of subject contract -not less "
        "than of 50 (fifty) per cent of the respective limits prescribed in case of individual "
        "contractors may be accepted; (iii) financial soundness;",
    ]
    for clause in jv_clauses:
        score = technical_relevance_score(clause)
        assert score < 0, f"JV pre-qualification bullet should score negative, got {score}: {clause[:70]!r}"


# ---------------------------------------------------------------------------------
# Case 3 (same RCF NIT): the IS-code citation pattern required a space or colon after
# "IS" (e.g. "IS 800", "IS:800") and silently missed every hyphenated citation, which is
# how this document's entire fabrication/welding annexure cites standards ("IS-800",
# "IS-814", "IS-9595", "IS-7318"...). Real, IS-code-dense technical clauses were scoring
# 0 -- the same as administrative boilerplate -- purely because of the hyphen.
# ---------------------------------------------------------------------------------
def test_hyphenated_is_citations_are_recognised():
    clauses_with_expected_min_score = [
        ("Electrodes used for welding shall comply with IS-814 or IS-815 shall be of, "
         "Advani Oerlicon make or equivalent.", 2),
        ("The erection of steel work shall be in accordance with Bureau of Indian Standard "
         "Specifications nos. IS -800 and IS-816.", 2),
        ("No welder shall be employed to carry out welding in any position except those who "
         "are fully qualified to weld in that position as per IS-7318, Part-1 qualifying tests "
         "for metal arc welders.", 2),
    ]
    for clause, min_score in clauses_with_expected_min_score:
        score = technical_relevance_score(clause)
        assert score >= min_score, (
            f"Hyphenated IS citation should score >= {min_score}, got {score}: {clause[:70]!r}"
        )


# ---------------------------------------------------------------------------------
# Case 4 (same RCF NIT, painting annexure): DFT paint-thickness specs are given in
# microns throughout ("70 microns per coat"), a standard coating-spec unit, but the
# dimension pattern only recognised "mm" and "kV".
# ---------------------------------------------------------------------------------
def test_micron_dimensions_are_recognised():
    clause = "One coat of Ethyl silicate inorganic zinc primer having DFT of 70 microns per coat."
    score = technical_relevance_score(clause)
    assert score > 0, f"A DFT-in-microns spec should score positively, got {score}"


# ---------------------------------------------------------------------------------
# Case 5: real technical content should still clearly outrank JV/eligibility content
# after the fixes above -- this is the actual selection-ordering bug, not just the
# isolated scoring bug. Build a minimal synthetic PDF combining one JV-eligibility
# paragraph and one welding-spec paragraph (as they actually appear, in that document
# order) and confirm the welding clause is selected and ranked ahead of the JV clause.
# ---------------------------------------------------------------------------------
def test_technical_content_outranks_eligibility_content_end_to_end():
    doc = fitz.open()
    page = doc.new_page()
    text = (
        "2. Qualifying factors for lead partner: (i) particular construction experience; "
        "(ii) financial capability to meet cash flow requirement of subject contract not less "
        "than of 50 (fifty) per cent of the respective limits prescribed in case of individual "
        "contractors may be accepted; (iii) financial soundness of the bidder firm.\n\n"
        "All bolts, nuts, washers etc. shall be in conformity with IS-800. The heads of bolts "
        "shall be forged and solid, truly concentric and square with the shanks and hexagonal "
        "in form and shall be screwed with whitworth threads well and cleanly cut."
    )
    page.insert_textbox(fitz.Rect(40, 40, 550, 780), text, fontsize=11)

    result = TenderDocumentParser.parse_pdf_bytes(doc.tobytes(), filename="jv_vs_welding.pdf")
    all_selected = [*result.technical_clauses, *[b["description"] for b in result.boq_items]]

    bolt_idx = next((i for i, c in enumerate(all_selected) if "whitworth" in c.lower()), None)
    jv_idx = next((i for i, c in enumerate(all_selected) if "qualifying factors" in c.lower()), None)

    assert bolt_idx is not None, f"Real welding/bolts spec was not extracted at all: {all_selected}"
    if jv_idx is not None:
        assert bolt_idx < jv_idx, (
            "JV eligibility text ranked ahead of a genuine IS-cited technical clause: "
            f"bolt_idx={bolt_idx}, jv_idx={jv_idx}"
        )


# ---------------------------------------------------------------------------------
# Floor check: the two real government tenders sourced and verified earlier this
# session (IISER Kolkata civil works NIT, IIT Kanpur maintenance BoQ) must keep
# extracting a full set of genuinely technical clauses/items. A collapse toward zero
# here means a change broke real-world extraction, not just the synthetic cases above.
# ---------------------------------------------------------------------------------
def test_real_documents_still_extract_richly():
    import os

    real_docs_dir = os.path.join(os.path.dirname(__file__), "real_test_docs")
    for filename, min_clauses, min_boq in [
        ("iiserkol_nit_civil.pdf", 15, 15),
        ("iitk_tender.pdf", 15, 15),
    ]:
        path = os.path.join(real_docs_dir, filename)
        with open(path, "rb") as f:
            data = f.read()
        result = TenderDocumentParser.parse_pdf_bytes(data, filename=filename)
        assert len(result.technical_clauses) >= min_clauses, (
            f"{filename}: technical_clauses collapsed to {len(result.technical_clauses)} "
            f"(floor is {min_clauses}) -- likely a scoring/extraction regression."
        )
        assert len(result.boq_items) >= min_boq, (
            f"{filename}: boq_items collapsed to {len(result.boq_items)} (floor is {min_boq})."
        )


def _run_all():
    tests = [
        test_schedule_table_not_read_as_technical_clauses,
        test_jv_prequalification_bullets_score_negative,
        test_hyphenated_is_citations_are_recognised,
        test_micron_dimensions_are_recognised,
        test_technical_content_outranks_eligibility_content_end_to_end,
        test_real_documents_still_extract_richly,
    ]
    failures = []
    for t in tests:
        try:
            t()
            print(f"[PASS] {t.__name__}")
        except AssertionError as e:
            failures.append(t.__name__)
            print(f"[FAIL] {t.__name__}: {e}")
    print()
    if failures:
        print(f"{len(failures)}/{len(tests)} FAILED: {', '.join(failures)}")
        raise SystemExit(1)
    print(f"All {len(tests)} tender-parser regression cases passed.")


if __name__ == "__main__":
    _run_all()
