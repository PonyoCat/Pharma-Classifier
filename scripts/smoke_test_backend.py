import json, time, requests

BASE = "http://127.0.0.1:8000"

def check_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    r.raise_for_status()
    print("Health:", r.json())

def post_analyze():
    body = {"text":"Aspirin 100 mg helped with headache yesterday."}
    r = requests.post(f"{BASE}/analyze", json=body, timeout=10)
    r.raise_for_status()
    data = r.json()
    print("Analyze id:", data["id"])
    return data["id"]

def get_reports():
    r = requests.get(f"{BASE}/reports?limit=5", timeout=10)
    r.raise_for_status()
    items = r.json()
    print("Reports:", len(items))
    return items

def get_by_id(rid):
    r = requests.get(f"{BASE}/reports/{rid}", timeout=10)
    r.raise_for_status()
    print("Get by id ok")

if __name__ == "__main__":
    check_health()
    rid = post_analyze()
    time.sleep(0.5)
    items = get_reports()
    get_by_id(rid)
    print("SMOKE OK")
