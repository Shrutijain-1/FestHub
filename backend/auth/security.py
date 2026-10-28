"""Password hashing + JWT token creation/verification."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from backend.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY

ALGORITHM = "HS256"
BCRYPT_MAX_BYTES = 72  # bcrypt cannot handle passwords longer than this


def hash_password(plain_password: str) -> str:
    """Turn a plain password into a secure hash for storage."""
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Check a login attempt against the stored hash. Never raises."""
    data = plain_password.encode("utf-8")
    if len(data) > BCRYPT_MAX_BYTES:
        return False  # it can't match, and bcrypt would raise an error
    try:
        return bcrypt.checkpw(data, password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: int, role: str) -> str:
    """Build a signed JWT containing the user's id and role.

    The token is like a stamped ticket: the server signs it with SECRET_KEY,
    so it can later verify the ticket wasn't tampered with, without needing
    to look anything up in the database on every request.
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Return the token's payload if valid, or None if invalid/expired."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None