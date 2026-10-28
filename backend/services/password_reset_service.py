"""Demo-mode password reset using a short-lived 6-digit code kept in memory."""
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.auth.security import hash_password
from backend.core.config import DEMO_MODE
from backend.models import User

logger = logging.getLogger("eventflow.auth")

CODE_LIFETIME = timedelta(minutes=10)
MAX_ATTEMPTS = 5

# user id -> {"hash": ..., "expires": ..., "attempts": ...}
# Kept in memory, so pending codes are lost when the backend restarts.
_pending: dict[int, dict] = {}


class ResetError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _hash(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _find_user(db: Session, email: str) -> User | None:
    return db.query(User).filter(func.lower(User.email) == email.strip().lower()).first()


def request_code(db: Session, email: str) -> str | None:
    """Create a reset code if the email is registered.
    The code is returned to the caller only in demo mode."""
    user = _find_user(db, email)
    if user is None:
        return None

    code = f"{secrets.randbelow(1_000_000):06d}"
    _pending[user.id] = {
        "hash": _hash(code),
        "expires": datetime.now() + CODE_LIFETIME,
        "attempts": 0,
    }
    # There is no email service, so this log line plays the role of the email.
    logger.info("[EMAIL SIMULATION] Password reset code for %s: %s", user.email, code)
    return code if DEMO_MODE else None


def reset_password(db: Session, email: str, code: str, new_password: str) -> None:
    user = _find_user(db, email)
    entry = _pending.get(user.id) if user else None

    # Same message for "no such user" and "no code", so emails are not revealed
    if user is None or entry is None or entry["expires"] < datetime.now():
        if user is not None:
            _pending.pop(user.id, None)
        raise ResetError("This code is invalid or has expired. Please request a new one.")

    if entry["attempts"] >= MAX_ATTEMPTS:
        _pending.pop(user.id, None)
        raise ResetError("Too many wrong attempts. Please request a new code.", 429)

    if not hmac.compare_digest(entry["hash"], _hash(code.strip())):
        entry["attempts"] += 1
        raise ResetError("That code is not correct.")

    user.password_hash = hash_password(new_password)
    db.commit()
    _pending.pop(user.id, None)  # a code works only once