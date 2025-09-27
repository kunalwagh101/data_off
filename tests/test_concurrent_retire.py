import threading
from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine
from app import seed_data

client = TestClient(app)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    try:
        seed_data.seed()
    except FileNotFoundError:
        pass


def create_record(payload):
    r = client.post('/records', json=payload)
    r.raise_for_status()
    return r.json()['id']


def retire_record(rid, results, idx):
    r = client.post(f'/records/{rid}/retire')
    results[idx] = r.status_code


def test_concurrent_retire():
    payload = {
        "project_name": "Concurrent Retire Project",
        "registry": "VCS",
        "vintage": 2025,
        "quantity": 1,
        "serial_number": "CON-0001"
    }
    rid = create_record(payload)
    n = 5
    results = [None] * n
    threads = []
    for i in range(n):
        t = threading.Thread(target=retire_record, args=(rid, results, i))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    # Exactly one should be 200 (success), others 409
    assert results.count(200) == 1
    assert results.count(409) == n - 1
