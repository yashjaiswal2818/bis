"""Test script for Regional Indic and Complex Natural Language Queries."""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCENARIOS = [
    # 1. Marathi (Devanagari)
    {
        "language": "Marathi",
        "query": "काँक्रीट मजबुतीकरणासाठी स्टील बार Fe 500D",
        "description": "TMT Steel bars for concrete reinforcement Fe 500D",
        "expected_code": "IS 1786",
    },
    {
        "language": "Marathi",
        "query": "पिण्याचे स्वच्छ पाणी गुणवत्ता चाचणी",
        "description": "Drinking water quality testing",
        "expected_code": ["IS 10500", "IS 3025"],
    },
    {
        "language": "Marathi",
        "query": "घरातील वायरिंगसाठी पीव्हीसी इन्सुलेटेड वायर 1100V",
        "description": "PVC insulated wires for house wiring 1100V",
        "expected_code": "IS 694",
    },

    # 2. Tamil
    {
        "language": "Tamil",
        "query": "1100V மின் கம்பி வீட்டு வயரிங்",
        "description": "1100V electric wire for house wiring",
        "expected_code": "IS 694",
    },
    {
        "language": "Tamil",
        "query": "குடிநீர் தரம் விவரக்குறிப்பு",
        "description": "Drinking water quality specification",
        "expected_code": "IS 10500",
    },

    # 3. Telugu
    {
        "language": "Telugu",
        "query": "భవన నిర్మాణానికి స్టీల్ బార్స్ Fe 500D",
        "description": "Steel bars Fe 500D for building construction",
        "expected_code": "IS 1786",
    },

    # 4. Complex Conversational Natural Language Inquiries
    {
        "language": "English (Conversational)",
        "query": "What is the mandatory standard for secondary lithium batteries used in portable electronics under MeitY CRS?",
        "description": "Lithium ion batteries for portable devices under Compulsory Registration Scheme",
        "expected_code": "IS 16046",
    },
    {
        "language": "English (Conversational)",
        "query": "Can you provide the standard for ductile detailing of reinforced concrete structures subjected to seismic forces?",
        "description": "Ductile detailing for RCC earthquake resistance",
        "expected_code": "IS 13920",
    },
    {
        "language": "English (Conversational)",
        "query": "We are procuring 43 grade and 53 grade ordinary portland cement for structural flyover piers",
        "description": "Ordinary Portland Cement 43 and 53 grade",
        "expected_code": ["IS 8112", "IS 12269", "IS 269"],
    },
]

def run_tests():
    print("=" * 80)
    print("  EVALUATING REGIONAL INDIC & COMPLEX CONVERSATIONAL SCENARIOS")
    print("=" * 80)

    results = []
    for idx, item in enumerate(SCENARIOS, 1):
        lang = item["language"]
        q = item["query"]
        desc = item["description"]
        expected = item["expected_code"]
        expected_list = [expected] if isinstance(expected, str) else expected

        req = urllib.request.Request(
            "http://127.0.0.1:8000/search",
            data=json.dumps({"query": q, "top_k": 5}).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                hits = data.get("hits", [])
                hit_codes = [h["is_code"] for h in hits]
                top_code = hits[0]["is_code"] if hits else "None"
                top_title = hits[0]["title"] if hits else "None"
                confidence = hits[0]["confidence"] if hits else "LOW"

                is_match = any(any(exp in c for exp in expected_list) for c in hit_codes)
                rank = None
                for r_idx, c in enumerate(hit_codes, 1):
                    if any(exp in c for exp in expected_list):
                        rank = r_idx
                        break

                status = f"PASS (Rank #{rank})" if is_match else "FAIL"
                results.append({
                    "idx": idx,
                    "language": lang,
                    "query": q,
                    "desc": desc,
                    "status": status,
                    "top_code": top_code,
                    "top_title": top_title,
                    "retrieved": hit_codes[:3],
                    "confidence": confidence,
                })

                print(f"\n[{status}] Scenario {idx} [{lang}]")
                print(f"      Query: \"{q}\"")
                print(f"      Intent: {desc}")
                print(f"      Expected: {expected}")
                print(f"      Top Result: {top_code} | {top_title[:55]} ({confidence})")
                print(f"      Top 3 Hits: {hit_codes[:3]}")

        except Exception as e:
            print(f"\n[FAIL] Scenario {idx} [{lang}]: Error: {e}")
            results.append({"idx": idx, "language": lang, "query": q, "status": f"ERROR ({e})"})

    print("\n" + "=" * 80)
    print("  SUMMARY REPORT")
    print("=" * 80)
    for r in results:
        print(f"  #{r['idx']:02d} [{r['language']:<20}] {r['status']:<15} ➔ Top: {r.get('top_code', 'N/A')}")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
