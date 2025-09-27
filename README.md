# Offset — Carbon Credit Ledger (FastAPI)



---

## Prerequisites

- Python 3.10+ (3.11 recommended)
- Git (optional)
- On Windows: PowerShell or Windows Terminal is recommended

---

## 1) Create & activate a virtual environment

```bash
# macOS / Linux
python -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---using the vscode how can i setup the github andupload this projec to the github

## 2) Install Python dependencies

```bash
pip install -r requirements.txt
# ensure httpx is present for FastAPI TestClient
pip install httpx
```

> If you prefer a single step on a fresh environment, run:
>
> ```bash
> pip install -r requirements.txt httpx
> ```

---

## 3) (Recommended) Ensure database driver configuration

The project defaults to a synchronous SQLite engine. `app/db.py` sets `DATABASE_URL` default to `sqlite:///./offset.db`.

- If you see an error complaining about `aiosqlite`, either install it (`pip install aiosqlite`) **or** switch `app/db.py` to the synchronous SQLite URI (`sqlite:///./offset.db`). The repository is written for the synchronous engine and the latter is recommended for local testing.

---

## 4) Seed the sample data

The project includes a `sample-registry.json` file in the repo root. `app/seed_data.py` will search the current working directory and parent folders for `sample-registry.json`. You can also explicitly provide its path using the `SAMPLE_REGISTRY_PATH` env var.

```bash
# simple seed (auto-locates sample-registry.json)
python -m app.seed_data

# explicit path example (Windows PowerShell):
# $env:SAMPLE_REGISTRY_PATH = "C:\full\path\to\sample-registry.json" ; python -m app.seed_data
```

Expected output:

```
Seeding DB from: /path/to/sample-registry.json
Seeding complete
```

---

## 5) Run the server (development)

```bash
uvicorn app.main:app --reload
```

Open the interactive API docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---


### Direct testing :- try using the  command to run the test 
```
  python smoke.py
```


## API Reference (summary)

### POST /records

Create a record. Payload:

```json
{
  "project_name": "Mangrove Restoration Project",
  "registry": "VCS",
  "vintage": 2023,
  "quantity": 100,
  "serial_number": "VCS-0001"
}
```

- Returns: `200 OK` with the created record (idempotent — same input => same id)
- Validation errors: `422 Unprocessable Entity`

---

### POST /records/{id}/retire

Retire a record (append-only event).

- First retire: `200 OK` + record returned with `retired` event
- Duplicate retire: `409 Conflict` (already retired)
- Unknown id: `404 Not Found`

---

### GET /records/{id}

Return full record details including all events (created, retired, ...).

- Success: `200 OK` + record JSON
- Not found: `404 Not Found`

---

## How the deterministic ID works (brief)

We canonicalize the core fields (`project_name`, `registry`, `vintage`, `quantity`, `serial_number`) into a stable JSON string (normalize case and whitespace), then compute a SHA-256 hex digest of that string. This ensures identical payloads map to the same ID.

---

## Testing



### 1) Manual / Interactive (Swagger)

Start the server and use `http://127.0.0.1:8000/docs` to execute requests directly from the browser.

### 2) Manual via PowerShell / curl

Create a record (PowerShell):

```powershell
$body = '{"project_name":"Smoke Test","registry":"VCS","vintage":2025,"quantity":5,"serial_number":"SMK-01"}'
$r = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/records -Body $body -ContentType 'application/json'
$r | ConvertTo-Json -Depth 6
```

Fetch it:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/records/$($r.id)" | ConvertTo-Json -Depth 6
```

Retire it:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/records/$($r.id)/retire" | ConvertTo-Json -Depth 6
```

### 3) Automated tests (pytest)

Ensure `httpx` is installed (TestClient dependency), then run:

```bash
pytest -q
```

Included tests:

- `tests/test_api.py` — basic create / get / idempotency checks
- `tests/test_concurrent_retire.py` — simulates concurrent retire requests; expects one `200` and the rest `409`.

> If a test fails on Windows intermittently, re-run the test. For production-like concurrency checks, run the tests against Postgres (see Docker section below).

---

## Docker & Postgres (optional, for production-like testing)

Below is a minimal `docker-compose.yml` you can use (not included by default). It starts Postgres for a more realistic test of concurrency and transaction semantics.

```yaml
version: '3.8'
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: offset
      POSTGRES_PASSWORD: offset
      POSTGRES_DB: offsetdb
    ports:
      - 5432:5432
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

After starting Postgres, set your DB url and re-create tables:

```bash
export DATABASE_URL=postgresql+psycopg2://offset:offset@localhost:5432/offsetdb
# on Windows PowerShell:
# $env:DATABASE_URL = 'postgresql+psycopg2://offset:offset@localhost:5432/offsetdb'
# ensure psycopg2 is installed
pip install psycopg2-binary
python -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)"
python -m app.seed_data
```

Run the server and run `pytest` against this DB for more realistic behavior.

---

## Troubleshooting

- **`ModuleNotFoundError: No module named 'aiosqlite'`**: change `app/db.py` to use `sqlite:///./offset.db` (sync) or `pip install aiosqlite` and use the `sqlite+aiosqlite://` DSN.
- **`RuntimeError: The starlette.testclient module requires the httpx package to be installed.`**: `pip install httpx`.
- **DetachedInstanceError or missing events in responses**: ensure `crud` functions load events with `selectinload` before returning so Pydantic can serialize them outside of a DB session.

---

## Reflection answers (concise)

1. **Deterministic ID design:** canonicalize core fields and compute SHA-256. This yields the same id for semantically identical inputs.
2. **Why an event log:** immutable audit trail, replayable history and prevention of accidental data loss or double-selling.
3. **Concurrent retire race:** the unique DB constraint on `(record_id, event_type)` prevents duplicate retire events. On race, one transaction will succeed; the other will fail with `IntegrityError` and we return `409 Conflict`. For partial retirements, or more complex concurrency, use row locking (`SELECT ... FOR UPDATE`) or serializable isolation.

---

## Next steps (suggested enhancements)

- Add Alembic migrations and a `docker-compose.yml` with Postgres.
- Add API key authentication and request logging.
- Support partial retirements (retire a quantity) and add business rules to prevent over-retirement.
- Add CI that runs `pytest` with a Postgres service.

---

If you want, I will also:
- add a ready-to-run `docker-compose.yml` and Alembic scripts,
- produce a Postman collection and example requests,
- or paste this README into the project root `README.md` file for you.

Tell me which you'd like next and I will update the canvas accordingly.

