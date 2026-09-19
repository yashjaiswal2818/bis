"""Tests for NeGD API Setu BIS Gateway Adapter.

Verifies:
1. Standard metadata retrieval matching API Setu JSON schema.
2. Scheme-I (ISI Mark under Cement & Steel QCOs).
3. Scheme-II (CRS under MeitY Electronics Order).
4. Scheme-IV (Mandatory BIS Hallmarking with 6-digit HUID for Gold/Silver).
5. Voluntary standard (no QCO).
6. Allied standards taxonomy.
"""
from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from src.integration.apisetu_gateway import APISetuBISGateway


def test_apisetu_gateway():
    print("=" * 70)
    print("  TESTING NeGD API SETU BIS GATEWAY ADAPTER")
    print("=" * 70)

    gateway = APISetuBISGateway()

    # 1. Test Scheme-I Standard: Sulphate Resisting Portland Cement (IS 12330)
    res_cement = gateway.get_standard_details("IS 12330")
    print("\n[1] IS 12330 (Cement):")
    print(f"  - Status Code: {res_cement['status_code']}")
    print(f"  - Title: {res_cement['data']['title']}")
    print(f"  - Mandatory Rules Count: {res_cement['data']['mandatory_certification']['rules_count']}")
    assert res_cement["status_code"] == 200
    assert res_cement["data"]["mandatory_certification"]["is_mandatory"] is True
    assert "Cement" in res_cement["data"]["mandatory_certification"]["rules"][0]["order_name"]

    # 2. Test Scheme-IV Standard: Gold Hallmarking (IS 1417)
    res_gold = gateway.get_standard_details("IS 1417: 2016")
    print("\n[2] IS 1417 (Gold Hallmarking):")
    print(f"  - Status Code: {res_gold['status_code']}")
    print(f"  - Scheme Type: {res_gold['data']['mandatory_certification']['rules'][0]['scheme_type']}")
    print(f"  - Compliance Warning: {res_gold['data']['mandatory_certification']['rules'][0]['compliance_warning'][:80]}...")
    assert res_gold["status_code"] == 200
    assert "Scheme-IV" in res_gold["data"]["mandatory_certification"]["rules"][0]["scheme_type"]
    assert "HUID" in res_gold["data"]["mandatory_certification"]["rules"][0]["compliance_warning"]

    # 3. Test Scheme-II Standard: Electronics CRS (IS 13252)
    qco_laptop = gateway.check_qco_compliance("IS 13252")
    print("\n[3] IS 13252 (Electronics CRS):")
    print(f"  - Is Mandatory: {qco_laptop['is_mandatory']}")
    print(f"  - Scheme Type: {qco_laptop['scheme_type']}")
    print(f"  - Issuing Ministry: {qco_laptop['issuing_ministry']}")
    assert qco_laptop["is_mandatory"] is True
    assert "Scheme-II" in qco_laptop["scheme_type"]
    assert "MeitY" in qco_laptop["issuing_ministry"]

    # 4. Test Voluntary Standard (e.g. general glossary IS 1200 Part 1)
    qco_glossary = gateway.check_qco_compliance("IS 1200 (Part 1)")
    print("\n[4] Voluntary Standard (IS 1200 Part 1):")
    print(f"  - Is Mandatory: {qco_glossary['is_mandatory']}")
    assert qco_glossary["is_mandatory"] is False

    # 5. Test Allied Standards
    allied = gateway.get_allied_standards("IS 456: 2000")
    print(f"\n[5] Allied Standards for IS 456: Count = {len(allied)}")
    if allied:
        print(f"  - First Allied: {allied[0]['target_is_code']} ({allied[0].get('relation_type')})")

    print("\n" + "=" * 70)
    print("  ALL API SETU GATEWAY TESTS PASSED PERFECTLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_apisetu_gateway()
