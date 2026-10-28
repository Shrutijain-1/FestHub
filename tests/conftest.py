"""Test setup: a throwaway SQLite database and no real Gemini calls."""
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

# These must be set BEFORE the backend is imported, because config.py reads them once.
_db_file = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.as_posix()}"
os.environ["GEMINI_API_KEY"] = ""
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only-0123456789"
os.environ["DEMO_MODE"] = "true"

import pytest
from fastapi.testclient import TestClient

import backend.models  # noqa: F401  (registers the tables)
from backend.database import Base, engine
from backend.main import app


@pytest.fixture(autouse=True)
def fresh_database():
    """Every test starts with empty tables."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def make_user(client):
    """Registers a user through the real API and returns its token headers."""
    counter = {"n": 0}

    def _make(role: str = "student") -> dict:
        counter["n"] += 1
        email = f"{role}{counter['n']}@test.com"
        response = client.post("/api/auth/register", json={
            "name": f"Test {role.title()} {counter['n']}",
            "email": email,
            "password": "Password123",
            "role": role,
            "college": "Test College",
            "phone": "9876543210",
        })
        assert response.status_code == 201, response.text
        data = response.json()
        return {
            "headers": {"Authorization": f"Bearer {data['access_token']}"},
            "user": data["user"],
            "email": email,
        }

    return _make


@pytest.fixture
def event_payload():
    """Builds a valid event request body. Pass keyword arguments to change fields."""

    def _build(**overrides) -> dict:
        payload = {
            "title": "Test Workshop",
            "description": "A test event.",
            "highlights": "One\nTwo",
            "event_type": "Workshop",
            "new_college_name": "Test College",
            "event_date": (date.today() + timedelta(days=5)).isoformat(),
            "start_time": "10:00:00",
            "end_time": "16:00:00",
            "venue": "Hall 1",
            "city": "Pune",
            "capacity": 10,
            "registration_fee": 0,
            "registration_deadline": None,
            "status": "published",
        }
        payload.update(overrides)
        return payload

    return _build


@pytest.fixture
def make_event(client, event_payload):
    def _make(organizer: dict, **overrides) -> dict:
        response = client.post(
            "/api/events", json=event_payload(**overrides), headers=organizer["headers"]
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def register_for(client):
    def _register(event_id: int, user: dict, payment_method: str | None = None):
        return client.post(
            f"/api/events/{event_id}/register",
            json={
                "student_name": user["user"]["name"],
                "student_email": user["email"],
                "student_college": "Test College",
                "student_phone": "9876543210",
                "payment_method": payment_method,
            },
            headers=user["headers"],
        )

    return _register