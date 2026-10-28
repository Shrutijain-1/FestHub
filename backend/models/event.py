"""Event table: created by an organizer, hosted by a college."""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Text, Time,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    highlights = Column(Text, nullable=True)  # one highlight per line
    event_type = Column(String(50), nullable=False)  # Workshop, Hackathon, etc.

    event_date = Column(DateTime, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    venue = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)

    capacity = Column(Integer, nullable=False)
    registration_fee = Column(Float, default=0.0)
    registration_deadline = Column(DateTime, nullable=True)

    image_path = Column(String(300), nullable=True)
    status = Column(String(20), default="draft")  # "draft" or "published"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    organizer = relationship("User", back_populates="events")
    college = relationship("College", back_populates="events")
    registrations = relationship(
        "Registration", back_populates="event", cascade="all, delete-orphan"
    )