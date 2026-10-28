"""Endpoints that belong to the logged-in organizer."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_organizer
from backend.database import get_db
from backend.models import Event, User
from backend.schemas.event import EventOut
from backend.services import event_service

router = APIRouter(prefix="/api", tags=["Organizer"])


@router.get("/my-events", response_model=list[EventOut])
def my_events(db: Session = Depends(get_db), user: User = Depends(require_organizer)):
    """All of this organizer's events, drafts included, newest date first."""
    events = (
        db.query(Event)
        .filter(Event.organizer_id == user.id)
        .order_by(Event.event_date.desc())
        .all()
    )
    return [event_service.to_event_out(e, db) for e in events]