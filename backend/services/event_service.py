from datetime import date, datetime, time

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from backend.models import College, Event, Registration, User
from backend.schemas.event import EventIn, EventOut
from backend.utils.image_upload import delete_event_image

def today_start() -> datetime:
    """Midnight today, so events happening today still count as upcoming."""
    return datetime.combine(date.today(), time.min)


def month_start(base: datetime, offset: int) -> datetime:
    """First day of the month, `offset` months after `base`."""
    index = base.month - 1 + offset
    return datetime(base.year + index // 12, index % 12 + 1, 1)


def count_registered(db: Session, event_id: int) -> int:
    """Seats taken = registrations that are not cancelled."""
    return (
        db.query(func.count(Registration.id))
        .filter(Registration.event_id == event_id, Registration.status == "registered")
        .scalar()
        or 0
    )


def to_event_out(event: Event, db: Session) -> EventOut:
    """Convert a database Event into the API response shape."""
    taken = count_registered(db, event.id)
    return EventOut(
        id=event.id,
        title=event.title,
        description=event.description,
        highlights=event.highlights,
        event_type=event.event_type,
        event_date=event.event_date,
        start_time=event.start_time,
        end_time=event.end_time,
        venue=event.venue,
        city=event.city,
        college_id=event.college_id,
        college_name=event.college.name,
        organizer_name=event.organizer.name,
        capacity=event.capacity,
        registration_fee=event.registration_fee or 0.0,
        registration_deadline=event.registration_deadline,
        image_path=event.image_path,
        status=event.status,
        registered_count=taken,
        seats_available=max(event.capacity - taken, 0),
    )


def get_upcoming_published(db: Session, limit: int | None = None) -> list[Event]:
    query = (
        db.query(Event)
        .filter(Event.status == "published", Event.event_date >= today_start())
        .order_by(Event.event_date)
    )
    return query.limit(limit).all() if limit else query.all()


def search_events(
    db: Session,
    q: str | None = None,
    event_type: str | None = None,
    college_id: int | None = None,
    city: str | None = None,
    month: str | None = None,  # format "YYYY-MM"
    fee: str | None = None,  # "free" or "paid"
    limit: int = 20,
) -> list[Event]:
    """Upcoming published events matching every filter that was given."""
    query = (
        db.query(Event)
        .join(College, Event.college_id == College.id)
        .filter(Event.status == "published", Event.event_date >= today_start())
    )

    if q and q.strip():
        pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Event.title.ilike(pattern),
                Event.description.ilike(pattern),
                Event.venue.ilike(pattern),
                College.name.ilike(pattern),
            )
        )
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if college_id:
        query = query.filter(Event.college_id == college_id)
    if city:
        query = query.filter(Event.city.ilike(city))
    if month:
        start = datetime.strptime(month, "%Y-%m")  # raises ValueError if invalid
        query = query.filter(
            Event.event_date >= start, Event.event_date < month_start(start, 1)
        )
    if fee == "free":
        query = query.filter(or_(Event.registration_fee == 0, Event.registration_fee.is_(None)))
    elif fee == "paid":
        query = query.filter(Event.registration_fee > 0)

    return query.order_by(Event.event_date).limit(limit).all()

# ---------- Create / update / delete (organizers) ----------

EVENT_TYPES = {
    "Workshop", "Hackathon", "Seminar", "Technical",
    "Cultural", "Sports", "Competition", "Other",
}


def _validate(payload: EventIn, is_new: bool) -> None:
    if payload.event_type not in EVENT_TYPES:
        raise ValueError("Please choose a valid event type.")
    if payload.end_time <= payload.start_time:
        raise ValueError("End time must be after the start time.")
    if is_new and payload.event_date < date.today():
        raise ValueError("The event date cannot be in the past.")
    deadline = payload.registration_deadline
    if deadline and deadline.date() > payload.event_date:
        raise ValueError("The registration deadline must be on or before the event date.")


def _resolve_college(db: Session, payload: EventIn) -> College:
    """Use the chosen college, or find/create one from the typed name."""
    if payload.college_id:
        college = db.get(College, payload.college_id)
        if college is None:
            raise ValueError("The selected college does not exist.")
        return college

    name = (payload.new_college_name or "").strip()
    if len(name) < 2:
        raise ValueError("Please choose a college or enter a new college name.")
    existing = db.query(College).filter(func.lower(College.name) == name.lower()).first()
    if existing:
        return existing
    college = College(name=name, city=payload.city.strip())
    db.add(college)
    db.flush()  # assigns college.id without committing yet
    return college


def _apply(event: Event, payload: EventIn, college: College) -> None:
    event.title = payload.title.strip()
    event.description = (payload.description or "").strip() or None
    event.highlights = (payload.highlights or "").strip() or None
    event.event_type = payload.event_type
    event.college_id = college.id
    event.event_date = datetime.combine(payload.event_date, time.min)
    event.start_time = payload.start_time
    event.end_time = payload.end_time
    event.venue = payload.venue.strip()
    event.city = payload.city.strip()
    event.capacity = payload.capacity
    event.registration_fee = payload.registration_fee
    event.registration_deadline = payload.registration_deadline
    event.status = payload.status


def create_event(db: Session, payload: EventIn, organizer: User) -> Event:
    _validate(payload, is_new=True)
    college = _resolve_college(db, payload)
    event = Event(organizer_id=organizer.id)
    _apply(event, payload, college)
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update_event(db: Session, event: Event, payload: EventIn) -> Event:
    _validate(payload, is_new=False)
    taken = count_registered(db, event.id)
    if payload.capacity < taken:
        raise ValueError(f"Capacity cannot be less than the {taken} students already registered.")
    college = _resolve_college(db, payload)
    _apply(event, payload, college)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event: Event) -> None:
    delete_event_image(event.image_path)
    db.delete(event)  # registrations are removed too (cascade in the model)
    db.commit()