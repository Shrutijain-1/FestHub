"""Business rules for registering, paying (simulated), cancelling and listing registrations."""
import secrets
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models import Event, Registration, User
from backend.schemas.registration import MyRegistrationOut, RegistrationIn
from backend.services.event_service import count_registered, today_start


class RegistrationError(Exception):
    """A rule was broken. Carries the message and the HTTP status to return."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _reference(prefix: str) -> str:
    """A random receipt number such as PAY-1A2B3C4D."""
    return f"{prefix}-{secrets.token_hex(4).upper()}"


def _money(amount: float) -> str:
    return f"{amount:,.0f}" if float(amount).is_integer() else f"{amount:,.2f}"


def register_student(
    db: Session, event_id: int, student: User, payload: RegistrationIn
) -> Registration:
    # 1. Event must exist and be published (drafts look like "not found")
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None or event.status != "published":
        raise RegistrationError("Event not found.", 404)

    # 2. Event must not be over, and the deadline must not have passed
    if event.event_date < today_start():
        raise RegistrationError("This event has already taken place.")
    if event.registration_deadline and event.registration_deadline < datetime.now():
        raise RegistrationError("Registration for this event has closed.")

    # 3. Not already registered
    existing = (
        db.query(Registration)
        .filter(Registration.event_id == event.id, Registration.student_id == student.id)
        .first()
    )
    if existing and existing.status == "registered":
        raise RegistrationError("You are already registered for this event.", 409)

    # 4. Seats must remain
    if count_registered(db, event.id) >= event.capacity:
        raise RegistrationError("This event is full.", 409)

    # 5. Paid events need a payment method. The amount always comes from the event.
    fee = float(event.registration_fee or 0)
    if fee > 0 and not payload.payment_method:
        raise RegistrationError(
            "This is a paid event. Please choose a payment method and complete the payment."
        )

    try:
        if existing:  # student cancelled earlier: reuse the same row
            registration = existing
            registration.status = "registered"
            registration.registration_date = datetime.now(timezone.utc)
        else:
            registration = Registration(event_id=event.id, student_id=student.id)
            db.add(registration)

        # Snapshot of the details typed in the form
        registration.student_name = payload.student_name.strip()
        registration.student_email = payload.student_email
        registration.student_college = (payload.student_college or "").strip() or None
        registration.student_phone = payload.student_phone

        # Simulated payment, saved in the same transaction as the registration
        if fee > 0:
            registration.amount_paid = fee
            registration.payment_status = "paid"
            registration.payment_method = payload.payment_method
            registration.payment_reference = _reference("PAY")
            registration.paid_at = datetime.now(timezone.utc)
        else:
            registration.amount_paid = 0.0
            registration.payment_status = "not_required"
            registration.payment_method = None
            registration.payment_reference = None
            registration.paid_at = None
        registration.refund_reference = None  # clears any refund from an earlier cancellation
        registration.refund_initiated_at = None

        db.flush()  # writes the row inside the transaction, before committing

        # Re-check now that our row is in. If we went over capacity, undo it.
        if count_registered(db, event.id) > event.capacity:
            db.rollback()
            raise RegistrationError("This event is full.", 409)

        db.commit()
    except IntegrityError:
        # The database's unique (event_id, student_id) rule caught a duplicate
        db.rollback()
        raise RegistrationError("You are already registered for this event.", 409)

    db.refresh(registration)
    return registration


def cancel_registration(db: Session, registration_id: int, student: User) -> Registration:
    registration = db.get(Registration, registration_id)
    if registration is None:
        raise RegistrationError("Registration not found.", 404)
    if registration.student_id != student.id:
        raise RegistrationError("You can only cancel your own registrations.", 403)
    if registration.status == "cancelled":
        raise RegistrationError("This registration is already cancelled.")

    registration.status = "cancelled"  # the row stays, so history is kept

    # A paid registration starts a (simulated) refund of what the student actually paid
    if registration.payment_status == "paid":
        registration.payment_status = "refund_initiated"
        registration.refund_reference = _reference("RFD")
        registration.refund_initiated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(registration)
    return registration


def list_for_student(db: Session, student: User) -> list[Registration]:
    return (
        db.query(Registration)
        .filter(Registration.student_id == student.id)
        .order_by(Registration.registration_date.desc())
        .all()
    )


def list_for_event(db: Session, event_id: int) -> list[Registration]:
    return (
        db.query(Registration)
        .filter(Registration.event_id == event_id)
        .order_by(Registration.registration_date.desc())
        .all()
    )


def to_my_registration_out(registration: Registration) -> MyRegistrationOut:
    event = registration.event
    amount = registration.amount_paid or 0.0

    refund_message = None
    if registration.payment_status == "refund_initiated":
        refund_message = (
            f"Your money (₹{_money(amount)}) will be transferred to your account within 24 hours."
        )

    return MyRegistrationOut(
        id=registration.id,
        event_id=event.id,
        event_title=event.title,
        event_type=event.event_type,
        college_name=event.college.name,
        event_date=event.event_date,
        start_time=event.start_time,
        venue=event.venue,
        city=event.city,
        status=registration.status,
        registration_date=registration.registration_date,
        amount_paid=amount,
        payment_status=registration.payment_status or "not_required",
        payment_method=registration.payment_method,
        payment_reference=registration.payment_reference,
        refund_reference=registration.refund_reference,
        refund_message=refund_message,
    )