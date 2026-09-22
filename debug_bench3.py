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

q = TEST_QUERIES[0]
query_text = q["query"]
expected = q.get("expected_standards", q.get("expected_code", []))
print(f"Expected: {expected}")
req = urllib.request.Request(
    'http://127.0.0.1:8000/search',
    data=json.dumps({"query": query_text, "top_k": 3}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read().decode('utf-8'))
top_hit = data.get("hits", [])[0]
is_code = top_hit.get("is_code", "")
base_code = top_hit.get("base_code", "")
print(f"top_hit is_code: {is_code}, base_code: {base_code}")

is_match = False
if isinstance(expected, str):
    expected = [expected]

for exp in expected:
    if exp in is_code or exp in base_code or is_code.startswith(exp):
        is_match = True
        break

print(f"Is match? {is_match}")
