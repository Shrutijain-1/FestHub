"""Request and response shapes for events."""
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    """Used for both creating and editing an event."""
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    highlights: str | None = None
    event_type: str
    college_id: int | None = None          # an existing college...
    new_college_name: str | None = None    # ...or a new one
    event_date: date
    start_time: time
    end_time: time
    venue: str = Field(min_length=2, max_length=200)
    city: str = Field(min_length=2, max_length=100)
    capacity: int = Field(ge=1, le=100000)
    registration_fee: float = Field(ge=0)
    registration_deadline: datetime | None = None
    status: Literal["draft", "published"] = "draft"


class StatusUpdate(BaseModel):
    status: Literal["draft", "published"]


class EventOut(BaseModel):
    id: int
    title: str
    description: str | None
    highlights: str | None
    event_type: str
    event_date: datetime
    start_time: time | None
    end_time: time | None
    venue: str
    city: str
    college_id: int
    college_name: str
    organizer_name: str
    capacity: int
    registration_fee: float
    registration_deadline: datetime | None
    image_path: str | None
    status: str
    registered_count: int
    seats_available: int