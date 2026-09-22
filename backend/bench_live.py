import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

def check_health():
    try:
        resp = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5)
        if resp.status != 200:
            print("ERROR: Health check failed with status:", resp.status)
            sys.exit(1)
    except Exception as e:
        print("ERROR: Health check failed:", e)
        sys.exit(1)

def run_benchmark():
    check_health()
    p1 = Path("backend/datasets/national_evaluation_test_set.json")
    p2 = Path("backend/datasets/public_test_set.json")
    
    TEST_QUERIES = []
    if p1.exists():
        with open(p1, "r", encoding="utf-8") as f:
            TEST_QUERIES.extend(json.load(f))
    if p2.exists():
        with open(p2, "r", encoding="utf-8") as f:
            TEST_QUERIES.extend(json.load(f))
            
    if not TEST_QUERIES:
        print("ERROR: Zero queries to run!")
        sys.exit(1)
        
    correct = 0
    incorrect = 0
    errors = 0
    not_run = 0
    clamp_count = 0
    lowest_correct = 1.0
    below_75 = 0
    total_returned = 0
    
    print(f"Running {len(TEST_QUERIES)} benchmark queries...\n")
    for q in TEST_QUERIES:
        query_text = q["query"]
        expected_code = q.get("expected_standards", q.get("expected_code", []))
        
        req = urllib.request.Request(
            'http://127.0.0.1:8000/search',
            data=json.dumps({"query": query_text, "top_k": 3}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read().decode('utf-8'))
            hits = data.get("results", [])
            total_returned += 1
            if not hits:
                incorrect += 1
                continue
                
            top_hit = hits[0]
            top_score = top_hit.get("score", 0.0)
            if top_score >= 0.999: clamp_count += 1
            if top_score < 0.75: below_75 += 1
            
            is_match = False
            for exp in expected_code:
                if exp in top_hit.get("is_code", "") or exp in top_hit.get("base_code", "") or top_hit.get("is_code", "").startswith(exp):
                    is_match = True
                    break
            
            if is_match:
                correct += 1
                lowest_correct = min(lowest_correct, top_score)
            else:
                incorrect += 1
        except Exception as e:
            print(f"ERROR on query '{query_text}': {e}")
            errors += 1
            
    if errors > 0:
        print(f"\nINVALID RUN: Encountered {errors} errors.")
        sys.exit(1)
        
    if total_returned == 0:
        print("\nINVALID RUN: Zero queries returned data.")
        sys.exit(1)
        
    print(f"\nRESULTS:")
    print(f"Score: {correct}/{total_returned} ({(correct/total_returned)*100:.1f}%)")
    print(f"Clamped (0.999): {clamp_count}")
    print(f"Lowest Correct Score: {lowest_correct if correct > 0 else 'n/a'}")
    print(f"Below 0.75 Confidence: {below_75}")
    
    if correct < len(TEST_QUERIES):
        sys.exit(1)

if __name__ == "__main__":
    run_benchmark()
