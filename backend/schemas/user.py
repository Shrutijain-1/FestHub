"""Request/response shapes for auth endpoints."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _clean_phone(value: str | None) -> str | None:
    """Empty means 'no phone'. Otherwise it must be exactly 10 digits."""
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    if not (value.isdigit() and len(value) == 10):
        raise ValueError("Phone number must be exactly 10 digits.")
    return value


def _check_password_length(value: str) -> str:
    """bcrypt only uses the first 72 bytes, so reject anything longer."""
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password is too long. Please use at most 72 characters.")
    return value


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=72)
    role: str  # "student" or "organizer"
    college: str | None = None
    phone: str | None = None

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value):
        return _clean_phone(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        return _check_password_length(value)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    """Only these fields can be edited. Email and role cannot."""
    name: str = Field(min_length=2, max_length=100)
    college: str | None = Field(default=None, max_length=150)
    phone: str | None = None

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value):
        return _clean_phone(value)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=6, max_length=72)

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, value):
        return _check_password_length(value)


class MessageResponse(BaseModel):
    message: str
    demo_code: str | None = None  # only filled in demo mode


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # lets Pydantic read SQLAlchemy objects

    id: int
    name: str
    email: str
    role: str
    college: str | None
    phone: str | None
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut