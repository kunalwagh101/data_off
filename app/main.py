from fastapi import FastAPI, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from . import db, schemas, crud

app = FastAPI(title="Offset — Carbon Credit Ledger (prototype)")


def get_db():
    session = db.SessionLocal()
    try:
        yield session
    finally:
        session.close()


@app.post('/records', response_model=schemas.RecordOut)
def create_record(payload: schemas.RecordCreate, db: Session = Depends(get_db)):
    record, created = crud.create_record(db, payload)
    if not record:
        raise HTTPException(status_code=400, detail="couldn't create record")
    return record


@app.post('/records/{record_id}/retire', response_model=schemas.RecordOut)
def retire(record_id: str = Path(..., min_length=10), db: Session = Depends(get_db)):
    record, status = crud.retire_record(db, record_id)
    if status == "not_found":
        raise HTTPException(status_code=404, detail="record not found")
    if status == "already_retired":
        raise HTTPException(status_code=409, detail="record already retired")
    return record


@app.get('/records/{record_id}', response_model=schemas.RecordOut)
def get_record(record_id: str, db: Session = Depends(get_db)):
    record = crud.get_record_with_events(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="record not found")
    return record
