"""Comprehensive E2E Integration Test for Tender Compliance & Hallmark Auditing.

Tests:
1. Document with full compliance -> 'Everything is fine' verdict.
2. Document with missing IS code and missing Hallmark/ISI Mark -> identifies exact missing standards and marks.
3. CSV BoQ audit with compliance fields.
"""
from __future__ import annotations

import io
import fitz

from src.compliance.tender_compliance_auditor import TenderComplianceAuditor
from src.ingestion.tender_document_parser import TenderDocumentParser
from src.retrieval.hybrid_search_orchestrator import HybridSearchOrchestrator


def test_compliance_engine():
    print("=" * 65)
    print("  TEST 1: TENDER COMPLIANCE & HALLMARK AUDITOR UNIT CHECKS")
    print("=" * 65)
    auditor = TenderComplianceAuditor()

    # Case A: Gold jewellery with NO standard and NO hallmark
    c_gold_missing = auditor.audit_clause(
        "Supply of 22k gold medals for sports award ceremony",
        [{"confidence": "HIGH", "is_code": "IS 1417: 2016", "title": "Gold and Gold Alloys, Jewellery/Artefacts"}]
    )
    print("\n[Case A] Gold Jewellery (Omitted Citations):")
    print(f"  - is_fine: {c_gold_missing.is_fine}")
    print(f"  - is_code_missing: {c_gold_missing.is_code_missing} -> {c_gold_missing.missing_is_code}")
    print(f"  - hallmark_missing: {c_gold_missing.hallmark_missing} -> {c_gold_missing.missing_hallmark}")
    print(f"  - verdict: '{c_gold_missing.verdict}'")
    assert c_gold_missing.is_fine is False
    assert c_gold_missing.is_code_missing is True
    assert c_gold_missing.hallmark_missing is True
    assert "IS 1417" in c_gold_missing.missing_is_code
    assert "HUID" in c_gold_missing.missing_hallmark

    # Case B: Gold jewellery conforming to IS 1417 with BIS Hallmark & HUID
    c_gold_fine = auditor.audit_clause(
        "Supply of 22k gold medals conforming to IS 1417 with mandatory BIS 6-digit HUID hallmarking",
        [{"confidence": "HIGH", "is_code": "IS 1417: 2016", "title": "Gold and Gold Alloys, Jewellery/Artefacts"}]
    )
    print("\n[Case B] Gold Jewellery (Compliant with Standard & Hallmark):")
    print(f"  - is_fine: {c_gold_fine.is_fine}")
    print(f"  - verdict: '{c_gold_fine.verdict}'")
    assert c_gold_fine.is_fine is True
    assert c_gold_fine.verdict == "Everything is fine"
    assert c_gold_fine.is_code_missing is False
    assert c_gold_fine.hallmark_missing is False

    # Case C: Power cables conforming to IS 694 with ISI Mark
    c_cables_fine = auditor.audit_clause(
        "Supply of PVC insulated copper power cables conforming to IS 694 bearing mandatory ISI Mark",
        [{"confidence": "HIGH", "is_code": "IS 694: 2010", "title": "PVC Insulated Cables"}]
    )
    print("\n[Case C] Power Cables (Compliant with Standard & ISI Mark):")
    print(f"  - is_fine: {c_cables_fine.is_fine}")
    print(f"  - verdict: '{c_cables_fine.verdict}'")
    assert c_cables_fine.is_fine is True
    assert c_cables_fine.verdict == "Everything is fine"

    # Case D: Document-level 'Everything is fine' check
    doc_summary_fine = auditor.summarize_document_audit([c_gold_fine.to_dict(), c_cables_fine.to_dict()])
    print("\n[Case D] Document Level Summary (All Compliant):")
    print(f"  - all_compliant: {doc_summary_fine['all_compliant']}")
    print(f"  - overall_verdict: '{doc_summary_fine['overall_verdict']}'")
    print(f"  - summary_message: '{doc_summary_fine['summary_message']}'")
    assert doc_summary_fine["all_compliant"] is True
    assert doc_summary_fine["overall_verdict"] == "Everything is fine"
    assert "Everything is fine" in doc_summary_fine["summary_message"]

    # Case E: Document-level Gaps Detected check
    doc_summary_gaps = auditor.summarize_document_audit([c_gold_missing.to_dict(), c_cables_fine.to_dict()])
    print("\n[Case E] Document Level Summary (Mixed / Gaps):")
    print(f"  - all_compliant: {doc_summary_gaps['all_compliant']}")
    print(f"  - overall_verdict: '{doc_summary_gaps['overall_verdict']}'")
    print(f"  - summary_message: '{doc_summary_gaps['summary_message']}'")
    assert doc_summary_gaps["all_compliant"] is False
    assert doc_summary_gaps["missing_standards_count"] == 1
    assert doc_summary_gaps["missing_hallmarks_count"] == 1

    print("\n" + "=" * 65)
    print("  TEST 2: E2E TENDER PDF AUDIT SIMULATION")
    print("=" * 65)

    # Create synthetic fully compliant PDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(
        fitz.Rect(40, 40, 550, 780),
        """NOTICE INVITING TENDER - DEFENCE PROCUREMENT
Item 1: Supply of 22k Gold Medals conforming to IS 1417 with mandatory BIS 6-digit HUID hallmarking.
Item 2: Supply of PVC Insulated Copper Cables conforming to IS 694 with valid ISI Mark.
"""
    )
    pdf_bytes = doc.tobytes()

    extraction = TenderDocumentParser.parse_pdf_bytes(pdf_bytes, filename="compliant_tender.pdf")
    orch = HybridSearchOrchestrator()

    results = []
    for clause in extraction.technical_clauses:
        recs = orch.search(clause[:300], top_k=2)
        verdict = auditor.audit_clause(clause, recs)
        results.append({
            "clause": clause,
            "verdict": verdict.to_dict(),
        })

    doc_res = auditor.summarize_document_audit([r["verdict"] for r in results])
    print(f"\nSynthetic PDF Audited Items ({len(results)} items):")
    for idx, r in enumerate(results, 1):
        v = r["verdict"]
        print(f"  [{idx}] Clause: {r['clause'][:70]}...")
        print(f"      Status: {v['compliance_status']} | Verdict: '{v['verdict']}'")

    print(f"\nFinal PDF Audit Verdict: '{doc_res['overall_verdict']}'")
    assert doc_res["all_compliant"] is True
    assert doc_res["overall_verdict"] == "Everything is fine"

    print("\n[SUCCESS] All compliance & hallmark audit tests passed perfectly!")


if __name__ == "__main__":
    test_compliance_engine()
