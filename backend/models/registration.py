"""Registration table: links a student to an event they signed up for."""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.database import Base


class Registration(Base):
    __tablename__ = "registrations"
    __table_args__ = (
        # A student can only have ONE registration row per event.
        UniqueConstraint("event_id", "student_id", name="uq_event_student"),
    )

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Snapshot of the student's details at the time of registration
    student_name = Column(String(100), nullable=False)
    student_email = Column(String(150), nullable=False)
    student_college = Column(String(150), nullable=True)
    student_phone = Column(String(20), nullable=True)

    registration_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), default="registered")  # "registered" or "cancelled"

    # Payment details. Payments are SIMULATED in this demo: no real money moves.
    amount_paid = Column(Float, default=0.0)
    payment_status = Column(String(20), default="not_required")  # not_required, paid, refund_initiated
    payment_method = Column(String(30), nullable=True)
    payment_reference = Column(String(40), nullable=True)
    paid_at = Column(DateTime, nullable=True)
    refund_reference = Column(String(40), nullable=True)
    refund_initiated_at = Column(DateTime, nullable=True)

    event = relationship("Event", back_populates="registrations")
    student = relationship("User", back_populates="registrations")