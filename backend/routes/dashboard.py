"""Dashboard statistics, different for students and organizers."""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.database import get_db
from backend.models import College, Event, Registration, User
from backend.services import event_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
def dashboard_stats(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == "organizer":
        my_events = db.query(Event).filter(Event.organizer_id == user.id).all()
        my_ids = [e.id for e in my_events]
        total_regs = 0
        if my_ids:
            total_regs = (
                db.query(func.count(Registration.id))
                .filter(Registration.event_id.in_(my_ids), Registration.status == "registered")
                .scalar()
            )
        today = event_service.today_start()
        return {"stats": [
            {"label": "My Events", "value": len(my_events)},
            {"label": "Published", "value": sum(e.status == "published" for e in my_events)},
            {"label": "Upcoming", "value": sum(e.event_date >= today for e in my_events)},
            {"label": "Total Registrations", "value": total_regs},
        ]}

    upcoming = event_service.get_upcoming_published(db)
    with_seats = [e for e in upcoming if event_service.count_registered(db, e.id) < e.capacity]
    my_regs = (
        db.query(func.count(Registration.id))
        .filter(Registration.student_id == user.id, Registration.status == "registered")
        .scalar()
    )
    return {"stats": [
        {"label": "Upcoming Events", "value": len(upcoming)},
        {"label": "Available Events", "value": len(with_seats)},
        {"label": "My Registrations", "value": my_regs},
        {"label": "Colleges", "value": db.query(func.count(College.id)).scalar()},
    ]}