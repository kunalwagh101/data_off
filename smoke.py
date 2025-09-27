import requests, json
BASE = "http://127.0.0.1:8000"
payload = {"project_name":"Smoke Test","registry":"VCS","vintage":2025,"quantity":5,"serial_number":"SMK-01"}
r = requests.post(f"{BASE}/records", json=payload); r.raise_for_status()
print("CREATE:", json.dumps(r.json(), indent=2))
rid = r.json()["id"]
r2 = requests.post(f"{BASE}/records/{rid}/retire")
print("RETIRE 1:", r2.status_code, r2.text)
r3 = requests.post(f"{BASE}/records/{rid}/retire")
print("RETIRE 2:", r3.status_code, r3.text)
r4 = requests.get(f"{BASE}/records/{rid}")
print("GET:", json.dumps(r4.json(), indent=2))
