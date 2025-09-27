from pydantic import BaseModel, Field, conint
from typing import Optional, List, Any
from datetime import datetime

class RecordCreate(BaseModel):
    project_name: str = Field(..., min_length=1)
    registry: str = Field(..., min_length=1)
    vintage: int
    quantity: conint(gt=0)
    serial_number: Optional[str] = None

class EventOut(BaseModel):
    id: int
    event_type: str
    payload: Optional[Any]
    created_at: datetime

    class Config:
        orm_mode = True

class RecordOut(BaseModel):
    id: str
    project_name: str
    registry: str
    vintage: int
    quantity: int
    serial_number: Optional[str]
    created_at: datetime
    events: List[EventOut]

    class Config:
        orm_mode = True
