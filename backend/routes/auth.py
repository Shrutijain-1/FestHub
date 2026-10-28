"""Registration, login, profile and password reset endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_current_user
from backend.auth.security import create_access_token, hash_password, verify_password
from backend.database import get_db
from backend.models import User
from backend.schemas.user import (
    ForgotPasswordRequest, MessageResponse, ProfileUpdate, ResetPasswordRequest,
    TokenResponse, UserLogin, UserOut, UserRegister,
)
from backend.services import password_reset_service
from backend.services.password_reset_service import ResetError

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if payload.role not in ("student", "organizer"):
        raise HTTPException(status_code=400, detail="Role must be 'student' or 'organizer'.")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        college=payload.college,
        phone=payload.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # Same error for "no such email" and "wrong password" on purpose:
    # this avoids revealing which emails are registered.
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Edit name, college and phone. Email and role can't be changed here."""
    user = db.get(User, current_user.id)
    user.name = payload.name.strip()
    user.college = (payload.college or "").strip() or None
    user.phone = payload.phone
    db.commit()
    db.refresh(user)
    return user


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    code = password_reset_service.request_code(db, payload.email)
    return MessageResponse(
        message="If this email is registered, a reset code has been created.",
        demo_code=code,
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    try:
        password_reset_service.reset_password(
            db, payload.email, payload.code, payload.new_password
        )
    except ResetError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)
    return MessageResponse(message="Password updated. You can now log in.")