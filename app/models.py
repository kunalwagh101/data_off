from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .db import Base

class Record(Base):
    __tablename__ = "records"
    id = Column(String(64), primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    registry = Column(String, nullable=False)
    vintage = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    serial_number = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    events = relationship("Event", back_populates="record", cascade="all, delete-orphan", order_by="Event.created_at")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String(64), ForeignKey("records.id"), nullable=False)
    event_type = Column(String, nullable=False)  # e.g. "created", "retired"
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    record = relationship("Record", back_populates="events")

    # Unique constraint prevents duplicate identical event types (eg. duplicate retired event)
    __table_args__ = (
        UniqueConstraint('record_id', 'event_type', name='uq_record_eventtype'),
    )
