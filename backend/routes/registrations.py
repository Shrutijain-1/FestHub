"""Student registration endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth.dependencies import require_student
from backend.database import get_db
from backend.models import User
from backend.schemas.registration import MyRegistrationOut, RegistrationIn
from backend.services import registration_service
from backend.services.registration_service import RegistrationError

router = APIRouter(prefix="/api", tags=["Registrations"])


@router.post("/events/{event_id}/register", response_model=MyRegistrationOut, status_code=201)
def register_for_event(
    event_id: int,
    payload: RegistrationIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_student),
):
    try:
        registration = registration_service.register_student(db, event_id, user, payload)
    except RegistrationError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)
    return registration_service.to_my_registration_out(registration)


@router.get("/my-registrations", response_model=list[MyRegistrationOut])
def my_registrations(db: Session = Depends(get_db), user: User = Depends(require_student)):
    registrations = registration_service.list_for_student(db, user)
    return [registration_service.to_my_registration_out(r) for r in registrations]


@router.delete("/registrations/{registration_id}", response_model=MyRegistrationOut)
def cancel_registration(
    registration_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_student),
):
    """Cancels (the row is kept with status 'cancelled', not erased)."""
    try:
        registration = registration_service.cancel_registration(db, registration_id, user)
    except RegistrationError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)
    return registration_service.to_my_registration_out(registration)