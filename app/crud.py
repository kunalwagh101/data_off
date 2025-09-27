from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload
from . import models, schemas, utils


def create_record(db: Session, record_in: schemas.RecordCreate):
    payload = record_in.dict()
    record_id = utils.deterministic_id(payload)

    existing = db.query(models.Record).filter(models.Record.id == record_id).one_or_none()
    if existing:
        # ensure events are loaded
        existing = db.query(models.Record).options(selectinload(models.Record.events)).filter(models.Record.id == record_id).one()
        return existing, False

    record = models.Record(
        id=record_id,
        project_name=record_in.project_name.strip(),
        registry=record_in.registry.strip().upper(),
        vintage=record_in.vintage,
        quantity=record_in.quantity,
        serial_number=record_in.serial_number,
    )

    db.add(record)
    # add a created event
    event = models.Event(record=record, event_type="created", payload=payload)
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # concurrent writer created the record first -> return it
        existing = db.query(models.Record).options(selectinload(models.Record.events)).filter(models.Record.id == record_id).one()
        return existing, False

    db.refresh(record)
    # load events
    record = db.query(models.Record).options(selectinload(models.Record.events)).filter(models.Record.id == record_id).one()
    return record, True


def retire_record(db: Session, record_id: str, actor_payload: dict = None):
    record = db.query(models.Record).filter(models.Record.id == record_id).one_or_none()
    if not record:
        return None, "not_found"

    event = models.Event(record_id=record_id, event_type="retired", payload=actor_payload or {})
    db.add(event)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # likely duplicate retired event
        record = db.query(models.Record).options(selectinload(models.Record.events)).filter(models.Record.id == record_id).one()
        return record, "already_retired"

    record = db.query(models.Record).options(selectinload(models.Record.events)).filter(models.Record.id == record_id).one()
    return record, "retired"


def get_record_with_events(db: Session, record_id: str):
    record = db.query(models.Record).options(selectinload(models.Record.events)).filter(models.Record.id == record_id).one_or_none()
    return record
