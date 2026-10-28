"""Request and response shapes for registrations."""
from datetime import datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegistrationIn(BaseModel):
    student_name: str = Field(min_length=2, max_length=100)
    student_email: EmailStr
    student_college: str | None = Field(default=None, max_length=150)
    student_phone: str
    # Needed only for paid events. The amount is never taken from the client.
    payment_method: Literal["UPI", "Card", "Net Banking"] | None = None

    @field_validator("student_phone")
    @classmethod
    def phone_must_be_10_digits(cls, value: str) -> str:
        value = value.strip()
        if not (value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must be exactly 10 digits.")
        return value


class MyRegistrationOut(BaseModel):
    """A registration together with the event and payment details a student needs to see."""
    id: int
    event_id: int
    event_title: str
    event_type: str
    college_name: str
    event_date: datetime
    start_time: time | None
    venue: str
    city: str
    status: str
    registration_date: datetime
    amount_paid: float
    payment_status: str
    payment_method: str | None
    payment_reference: str | None
    refund_reference: str | None
    refund_message: str | None


class EventRegistrationOut(BaseModel):
    """One row of the organizer's attendee table."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_name: str
    student_email: str
    student_college: str | None
    student_phone: str | None
    registration_date: datetime
    status: str
    amount_paid: float
    payment_status: str
    payment_reference: str | None