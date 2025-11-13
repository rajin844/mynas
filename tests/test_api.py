import requests
BASE = 'http://127.0.0.1:8000'
def test_ping():
    r = requests.get(f"{BASE}/api/ping")
    assert r.status_code == 200
