import json, urllib.request, sys
query_text = "Procurement of gold jewellery and artefacts requiring mandatory purity marking and 6-digit alphanumeric HUID hallmarking under DoCA Scheme-IV."
req = urllib.request.Request(
    'http://127.0.0.1:8000/search',
    data=json.dumps({"query": query_text, "top_k": 3}).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read().decode('utf-8'))
print(data.keys())
print(data.get("results"))
