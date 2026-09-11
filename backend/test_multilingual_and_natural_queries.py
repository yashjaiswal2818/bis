"""Test script for Multilingual and Natural Language Queries on live backend."""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TEST_QUERIES = [
    {
        "type": "Multilingual (Hindi Devanagari)",
        "query": "पीवीसी इंसुलेटेड बिजली के तार 1100 वोल्ट",
        "expected_code": "IS 694",
    },
    {
        "type": "Multilingual (Hindi Devanagari)",
        "query": "22 कैरेट सोने के आभूषण हॉलमार्किंग",
        "expected_code": "IS 1417",
    },
    {
        "type": "Multilingual (Hindi Devanagari)",
        "query": "पीने का साफ पानी गुणवत्ता परीक्षण",
        "expected_code": "IS 10500",
    },
    {
        "type": "Hinglish (Romanized Hindi)",
        "query": "bijli ke taar 1100V building wiring ke liye",
        "expected_code": "IS 694",
    },
    {
        "type": "Hinglish (Romanized Hindi)",
        "query": "sone ke gehne 22k hallmarking huid ke sath",
        "expected_code": "IS 1417",
    },
    {
        "type": "Natural Language Query",
        "query": "Which BIS standard should we follow for fire safety in school and hospital buildings?",
        "expected_code": ["IS 1641", "IS 1642", "IS 1643"],
    },
    {
        "type": "Natural Language Query",
        "query": "What are the official test methods for drinking water physical and chemical parameters?",
        "expected_code": "IS 10500",
    },
    {
        "type": "Natural Language Query",
        "query": "We want to procure 22 carat gold medals with mandatory 6-digit HUID hallmarking for merit awards",
        "expected_code": "IS 1417",
    },
]

def main():
    print("=" * 70)
    print("  TESTING MULTILINGUAL & NATURAL LANGUAGE QUERY RETRIEVAL")
    print("=" * 70)

    all_passed = True
    for i, item in enumerate(TEST_QUERIES, 1):
        q_type = item["type"]
        query = item["query"]
        expected = item["expected_code"]
        expected_list = [expected] if isinstance(expected, str) else expected

        req = urllib.request.Request(
            "http://127.0.0.1:8000/search",
            data=json.dumps({"query": query, "top_k": 3}).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                hits = data.get("hits", [])
                hit_codes = [h["is_code"] for h in hits]
                top_code = hits[0]["is_code"] if hits else "None"
                top_title = hits[0]["title"] if hits else "None"

                matched = any(any(exp in c for exp in expected_list) for c in hit_codes)
                status_icon = "PASS" if matched else "FAIL"
                if not matched:
                    all_passed = False

                print(f"\n[{status_icon}] Test {i} ({q_type}): '{query}'")
                print(f"      Expected to contain: {expected}")
                print(f"      Top Match: {top_code} | {top_title[:55]}")
                print(f"      Retrieved Codes: {hit_codes}")
        except Exception as e:
            print(f"\n[FAIL] Test {i} ({q_type}): Error: {e}")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print(" [SUCCESS] All multilingual and natural language query tests PASSED!")
    else:
        print(" [WARNING] Some tests failed. Review outputs above.")
    print("=" * 70)

if __name__ == "__main__":
    main()
