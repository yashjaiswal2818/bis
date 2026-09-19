import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from src.api.fastapi_application import app

print("Testing FastAPI Application endpoints via TestClient...")

with TestClient(app) as client:
    # 1. Health
    r_health = client.get("/health")
    print(f"1. /health -> {r_health.status_code}: {r_health.json()}")
    assert r_health.status_code == 200

    # 2. Search
    r_search = client.post("/search", json={"query": "33 grade ordinary portland cement", "top_k": 3})
    print(f"2. /search -> {r_search.status_code}, hits: {len(r_search.json().get('hits', []))}")
    assert r_search.status_code == 200
    top_hit = r_search.json()["hits"][0]
    print(f"   Top Hit: {top_hit['is_code']} ({top_hit['title']})")
    assert "269" in top_hit["is_code"]

    # 3. NeGD API Setu Standard details
    r_std = client.get("/api/v1/bis/standards/IS 12330")
    print(f"3. /api/v1/bis/standards/IS 12330 -> {r_std.status_code}, data: {r_std.json()['data']['title']}")
    assert r_std.status_code == 200
    assert r_std.json()["data"]["mandatory_certification"]["is_mandatory"] is True

    # 4. NeGD API Setu QCO Check
    r_qco = client.get("/api/v1/bis/qco/check?is_code=IS 1786")
    print(f"4. /api/v1/bis/qco/check?is_code=IS 1786 -> {r_qco.status_code}, mandatory: {r_qco.json()['is_mandatory']}, scheme: {r_qco.json()['scheme_type']}")
    assert r_qco.status_code == 200
    assert r_qco.json()["is_mandatory"] is True

    # 5. NeGD API Setu Allied
    r_allied = client.get("/api/v1/bis/standards/IS 456: 2000/allied")
    print(f"5. /api/v1/bis/standards/IS 456: 2000/allied -> {r_allied.status_code}, count: {len(r_allied.json())}")
    assert r_allied.status_code == 200

print("\n>>> ALL FASTAPI ENDPOINTS VERIFIED AND FUNCTIONING 100% PERFECTLY! <<<")

