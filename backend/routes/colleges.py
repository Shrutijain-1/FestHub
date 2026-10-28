"""College list, used by the filter dropdowns."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.database import get_db
from backend.models import College, User

router = APIRouter(prefix="/api/colleges", tags=["Colleges"])


@router.get("")
def list_colleges(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    colleges = db.query(College).order_by(College.name).all()
    return [{"id": c.id, "name": c.name, "city": c.city} for c in colleges]