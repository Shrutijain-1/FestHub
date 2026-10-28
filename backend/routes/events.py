"""Event endpoints: search, by-month, details, and organizer create/edit/delete."""
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user, require_organizer
from backend.database import get_db
from backend.models import Event, User
from backend.schemas.event import EventIn, EventOut, StatusUpdate
from backend.schemas.registration import EventRegistrationOut
from backend.services import event_service, registration_service
from backend.utils.image_upload import delete_event_image, save_event_image

router = APIRouter(prefix="/api/events", tags=["Events"])


def _get_owned_event(db: Session, event_id: int, user: User) -> Event:
    """404 if missing, 403 if it belongs to another organizer."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found.")
    if event.organizer_id != user.id:
        raise HTTPException(status_code=403, detail="You can only change your own events.")
    return event


@router.get("", response_model=list[EventOut])
def list_events(
    q: str | None = None,
    event_type: str | None = None,
    college_id: int | None = None,
    city: str | None = None,
    month: str | None = None,
    fee: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Upcoming published events, soonest first. All filters are optional."""
    try:
        events = event_service.search_events(
            db, q=q, event_type=event_type, college_id=college_id,
            city=city, month=month, fee=fee, limit=limit,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Month must look like 2026-11.")
    return [event_service.to_event_out(e, db) for e in events]


@router.get("/by-month")
def events_by_month(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Powers 'This Month at Colleges': current month + next month."""
    now = event_service.today_start()
    first = event_service.month_start(now, 0)
    second = event_service.month_start(now, 1)
    end = event_service.month_start(now, 2)

    events = (
        db.query(Event)
        .filter(Event.status == "published", Event.event_date >= now, Event.event_date < end)
        .order_by(Event.event_date)
        .all()
    )
    months = [
        {"label": first.strftime("%B %Y"), "events": []},
        {"label": second.strftime("%B %Y"), "events": []},
    ]
    for event in events:
        slot = 0 if event.event_date < second else 1
        months[slot]["events"].append(event_service.to_event_out(event, db))
    return {"months": months}


@router.post("", response_model=EventOut, status_code=201)
def create_event(
    payload: EventIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_organizer),
):
    try:
        event = event_service.create_event(db, payload, user)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return event_service.to_event_out(event, db)


# Must stay AFTER "/by-month", otherwise FastAPI reads "by-month" as an id.
@router.get("/{event_id}", response_model=EventOut)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """One event. Drafts are only visible to the organizer who owns them."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None or (event.status != "published" and event.organizer_id != user.id):
        raise HTTPException(status_code=404, detail="Event not found.")
    return event_service.to_event_out(event, db)


@router.put("/{event_id}", response_model=EventOut)
def update_event(
    event_id: int,
    payload: EventIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_organizer),
):
    event = _get_owned_event(db, event_id, user)
    try:
        event = event_service.update_event(db, event, payload)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    return event_service.to_event_out(event, db)


@router.patch("/{event_id}/status", response_model=EventOut)
def change_status(
    event_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_organizer),
):
    """Publish or unpublish."""
    event = _get_owned_event(db, event_id, user)
    event.status = payload.status
    db.commit()
    db.refresh(event)
    return event_service.to_event_out(event, db)


@router.delete("/{event_id}", status_code=204)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_organizer),
):
    event = _get_owned_event(db, event_id, user)
    event_service.delete_event(db, event)
    return Response(status_code=204)


@router.post("/{event_id}/image", response_model=EventOut)
async def upload_image(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_organizer),
):
    event = _get_owned_event(db, event_id, user)
    new_path = await save_event_image(file)
    delete_event_image(event.image_path)  # remove the old image
    event.image_path = new_path
    db.commit()
    db.refresh(event)
    return event_service.to_event_out(event, db)
@router.get("/{event_id}/registrations", response_model=list[EventRegistrationOut])
def event_registrations(
    event_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_organizer),
):
    """Attendee list. Only the organizer who owns the event can see it."""
    event = _get_owned_event(db, event_id, user)
    return registration_service.list_for_event(db, event.id)