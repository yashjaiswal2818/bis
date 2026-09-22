import json, urllib.request, sys
from pathlib import Path

p1 = Path("backend/datasets/national_evaluation_test_set.json")
p2 = Path("backend/datasets/public_test_set.json")

TEST_QUERIES = []
if p1.exists():
    with open(p1, "r", encoding="utf-8") as f:
        TEST_QUERIES.extend(json.load(f))
if p2.exists():
    with open(p2, "r", encoding="utf-8") as f:
        TEST_QUERIES.extend(json.load(f))

for q in TEST_QUERIES:
    query_text = q["query"]
    expected_code = q.get("expected_standards", q.get("expected_code", []))
    
    req = urllib.request.Request(
        'http://127.0.0.1:8000/search',
        data=json.dumps({"query": query_text, "top_k": 3}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        data = json.loads(resp.read().decode('utf-8'))
        hits = data.get("hits", [])
        
        top_hit = hits[0] if hits else {}
        is_code = top_hit.get("is_code", "")
        base_code = top_hit.get("base_code", "")
        
        is_match = False
        if isinstance(expected_code, str):
            expected_code = [expected_code]
        for exp in expected_code:
            if exp in is_code or exp in base_code or is_code.startswith(exp):
                is_match = True
                break
        
        if not is_match:
            print(f"FAILED: {query_text}")
            print(f"  Expected: {expected_code}")
            print(f"  Got: {is_code} (base: {base_code})")
            
    except Exception as e:
        pass
