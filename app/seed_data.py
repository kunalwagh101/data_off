import json
import os
from pathlib import Path
from .db import SessionLocal, Base, engine
from .models import Record, Event
from . import utils

SAMPLE_FILENAME = "sample-registry.json"
DEFAULT_FALLBACK = os.getenv("SAMPLE_REGISTRY_PATH", "./data/sample-registry.json")


def locate_sample_file(start_path: Path = None) -> str:
    """Search current directory and parent directories for SAMPLE_FILENAME.

    Order:
    1) If env var SAMPLE_REGISTRY_PATH set and file exists -> use it.
    2) Walk from start_path (defaults to CWD) up to root to find sample-registry.json.
    3) Fallback to DEFAULT_FALLBACK if exists.
    4) If not found, raise FileNotFoundError with helpful message.
    """
    # 1) env var
    env_path = os.getenv("SAMPLE_REGISTRY_PATH")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return str(p)

    # 2) walk up from start_path
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()
    root = current.root if hasattr(current, 'root') else Path(current.anchor)

    while True:
        candidate = current / SAMPLE_FILENAME
        if candidate.exists():
            return str(candidate)
        if current == current.parent:
            break
        current = current.parent

    # 3) fallback
    fallback = Path(DEFAULT_FALLBACK)
    if fallback.exists():
        return str(fallback)

    raise FileNotFoundError(
        f"Could not locate {SAMPLE_FILENAME}. Looked in CWD and parents and fallback {DEFAULT_FALLBACK}. "
        "Set SAMPLE_REGISTRY_PATH environment variable to point to your sample file."
    )


def seed(path: str = None):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if path is None:
            path = locate_sample_file()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            # ensure core fields exist and types are normalized
            payload = {
                'project_name': item.get('project_name'),
                'registry': item.get('registry'),
                'vintage': int(item.get('vintage')) if item.get('vintage') is not None else None,
                'quantity': int(item.get('quantity')) if item.get('quantity') is not None else 0,
                'serial_number': item.get('serial_number'),
            }
            rid = utils.deterministic_id(payload)
            existing = db.query(Record).filter(Record.id == rid).one_or_none()
            if existing:
                continue
            r = Record(
                id=rid,
                project_name=payload['project_name'],
                registry=payload['registry'].upper() if payload['registry'] else None,
                vintage=payload['vintage'],
                quantity=payload['quantity'],
                serial_number=payload.get('serial_number'),
            )
            e = Event(record=r, event_type="created", payload=payload)
            db.add(r)
            db.add(e)
        db.commit()
    finally:
        db.close()


if __name__ == '__main__':
    try:
        p = locate_sample_file()
        print("Seeding DB from:", p)
        seed(p)
        print("Seeding complete")
    except FileNotFoundError as exc:
        print(str(exc))
