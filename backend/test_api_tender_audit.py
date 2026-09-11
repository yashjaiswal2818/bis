import json
import urllib.request
import fitz

def test_api():
    print("=" * 65)
    print("  TESTING LIVE FASTAPI /tender-audit ENDPOINT")
    print("=" * 65)

    # 1. Compliant Tender
    doc = fitz.open()
    p = doc.new_page()
    p.insert_textbox(
        fitz.Rect(40, 40, 550, 780),
        "NOTICE INVITING TENDER\n"
        "Item 1: Supply of 22k Gold Medals conforming to IS 1417 with mandatory BIS 6-digit HUID hallmarking.\n"
        "Item 2: Supply of PVC Insulated Cables conforming to IS 694 with valid ISI Mark."
    )
    pdf_bytes = doc.tobytes()

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(b'Content-Disposition: form-data; name="file"; filename="test_compliant.pdf"\r\n')
    body.extend(b"Content-Type: application/pdf\r\n\r\n")
    body.extend(pdf_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        "http://127.0.0.1:8000/tender-audit",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("\n--- COMPLIANT TENDER RESPONSE ---")
        print(f"all_compliant: {data.get('all_compliant')}")
        print(f"overall_verdict: '{data.get('overall_verdict')}'")
        print(f"summary_message: '{data.get('summary_message')}'")
        for idx, c in enumerate(data.get("clauses_analyzed", []), 1):
            cv = c.get("compliance_verdict", {})
            print(f"  Item {idx}: status={cv.get('compliance_status')} | verdict='{cv.get('verdict')}'")

        assert data.get("all_compliant") is True
        assert data.get("overall_verdict") == "Everything is fine"

    # 2. Non-Compliant Tender (Missing IS & Missing Hallmark)
    doc2 = fitz.open()
    p2 = doc2.new_page()
    p2.insert_textbox(
        fitz.Rect(40, 40, 550, 780),
        "NOTICE INVITING TENDER\n"
        "Item 1: Supply of 22k Gold Medals for sports award ceremony without hallmarking.\n"
        "Item 2: Replacement of defective 415V LT main distribution panel and incoming power cables."
    )
    pdf2_bytes = doc2.tobytes()

    body2 = bytearray()
    body2.extend(f"--{boundary}\r\n".encode("utf-8"))
    body2.extend(b'Content-Disposition: form-data; name="file"; filename="test_missing.pdf"\r\n')
    body2.extend(b"Content-Type: application/pdf\r\n\r\n")
    body2.extend(pdf2_bytes)
    body2.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    req2 = urllib.request.Request(
        "http://127.0.0.1:8000/tender-audit",
        data=bytes(body2),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )

    with urllib.request.urlopen(req2, timeout=30) as resp2:
        data2 = json.loads(resp2.read().decode("utf-8"))
        print("\n--- NON-COMPLIANT TENDER RESPONSE ---")
        print(f"all_compliant: {data2.get('all_compliant')}")
        print(f"overall_verdict: '{data2.get('overall_verdict')}'")
        print(f"summary_message: '{data2.get('summary_message')}'")
        print(f"missing_standards_count: {data2.get('missing_standards_count')}")
        print(f"missing_hallmarks_count: {data2.get('missing_hallmarks_count')}")
        for idx, c in enumerate(data2.get("clauses_analyzed", []), 1):
            cv = c.get("compliance_verdict", {})
            print(f"  Item {idx}: status={cv.get('compliance_status')} | verdict='{cv.get('verdict')}'")

        assert data2.get("all_compliant") is False
        assert data2.get("overall_verdict") == "Compliance Gaps Detected"

    print("\n[SUCCESS] Live API tests passed completely!")

if __name__ == "__main__":
    test_api()
