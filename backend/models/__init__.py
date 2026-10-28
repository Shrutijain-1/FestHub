"""Imports every model so Base.metadata knows about all of them."""
from backend.models.user import User
from backend.models.college import College
from backend.models.event import Event
from backend.models.registration import Registration

__all__ = ["User", "College", "Event", "Registration"]