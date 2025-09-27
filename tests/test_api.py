from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine, SessionLocal
from app import seed_data

client = TestClient(app)


def setup_module(module):
    # create fresh tables and seed
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    # seed using our sample file next to project if available
    try:
        seed_data.seed()
    except FileNotFoundError:
        pass


def test_create_and_get():
    payload = {
        "project_name": "Test Project Alpha",
        "registry": "VCS",
        "vintage": 2025,
        "quantity": 10,
        "serial_number": "TEST-0001"
    }
    r = client.post('/records', json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body['project_name'] == payload['project_name']
    rid = body['id']

    r2 = client.get(f'/records/{rid}')
    assert r2.status_code == 200
    assert len(r2.json()['events']) >= 1


def test_idempotent_create():
    payload = {
        "project_name": "Test Project Alpha",
        "registry": "VCS",
        "vintage": 2025,
        "quantity": 10,
        "serial_number": "TEST-0001"
    }
    r1 = client.post('/records', json=payload)
    r2 = client.post('/records', json=payload)
    assert r1.json()['id'] == r2.json()['id']
