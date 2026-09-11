"""End-to-end test for tender PDF upload and standard auditing."""
from __future__ import annotations

import fitz

from src.ingestion.tender_document_parser import TenderDocumentParser
from src.retrieval.hybrid_search_orchestrator import HybridSearchOrchestrator

# Create synthetic Ordnance Factory Badmal NIT PDF
doc = fitz.open()

# Page 1
p1 = doc.new_page()
rect1 = fitz.Rect(40, 40, 550, 780)
p1_text = """Ordnance Factory Badmal
Unit of Munitions India Limited
Ministry of Defence
Badmal, Balangir (Odisha)-767070

NOTICE INVITING E-TENDER
No.3012/OFBL/TE-09(2026-27)/RD2609/EO(C) Date 09.09.2026

The Chief General Manager, Ordnance Factory Badmal, Balangir, Odisha invites sealed quotations in electronic form under the two bid system (Technical/Eligibility Bid and Financial/Price Bid) from the eligible enlisted contractors for the under mentioned Electrical Work:-

S.N | Name of Work | Estimated Amount (Rs.) | Earnest Money Deposit (Rs.) | Time for Completion in Days | Bid submission End date & time
01 | Replacement of Defective 415Volt LT Main Distribution Panel & 415 V LT Main Distribution Board, Street Light Incoming Cables, Main Incoming Power Cables and circuit Wirings at Officers Club of Ordnance Factory Badmal. | 27,49,816/- | 55,000/- | 240 Days | 12.10.2026 & 14:00 hrs

Earnest Money Deposit (EMD)
1. The EMD should be in the form of FDR (Fixed Deposit Receipt) from any Nationalized Bank.
2. The SEALED envelope containing EMD in Original should be submitted physically at OFBL.

Eligibility/Evaluation Criteria
1. EMD as stated above.
2. Valid Registration for execution of Electrical Works with any Govt. department/PSUs/MSME/NSIC/MIL Units.
3. Experience of having successfully completed Similar nature of Electrical works having an annual turnover of Rs 100 crore or more.
"""
p1.insert_textbox(rect1, p1_text)

# Page 2
p2 = doc.new_page()
rect2 = fitz.Rect(40, 40, 550, 780)
p2_text = """4. Average annual financial turnover during the last three years should be at least 30% of the estimated cost.
5. Updated PAN/TAN Card.
6. Valid Goods & Service Tax Identification Number (GSTIN).
7. Affidavit or self-attested certificate in firm's letter head that firm is not debarred/Blacklisted.
8. Self attested certificate that they have read terms laid down in MES SSR 2009 Part-I, CPWD Specifications, IAFW 2249.

Note:
1. Vendors are requested to obtain Class-III Digital Signature Certificate (DSC) on CPPP website https://etenders.gov.in.
2. Firms can enrol themselves as a vendor/contractor on CPPP website.
3. Price Bid will be submitted online only.
4. Warranty Period for this work will be 1 year. The Security deposit shall be submitted for 1 year.
"""
p2.insert_textbox(rect2, p2_text)

pdf_bytes = doc.tobytes()

print("Step 1: Parsing PDF...")
extraction = TenderDocumentParser.parse_pdf_bytes(pdf_bytes, filename="badmal_tender.pdf")
print(f"Extracted {len(extraction.technical_clauses)} technical clauses.")

print("\nStep 2: Auditing with Hybrid Search Orchestrator...")
orch = HybridSearchOrchestrator()

for i, clause in enumerate(extraction.technical_clauses, 1):
    print(f"\n[{i}] Item / Scope: {clause}")
    recs = orch.search(clause[:300], top_k=3)
    for r in recs:
        print(f"    * {r.is_code}: {r.title} (Confidence: {r.confidence})")

print("\n[SUCCESS] End-to-end NIT audit completed successfully!")
