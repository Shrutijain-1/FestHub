"""Registration, login, tokens, profile and password reset."""
from backend.database import SessionLocal
from backend.models import User


def _register_body(email="new@test.com", password="Password123", role="student"):
    return {"name": "New User", "email": email, "password": password, "role": role}


def test_register_returns_token_and_no_password(client):
    response = client.post("/api/auth/register", json=_register_body())
    assert response.status_code == 201
    body = response.json()
    assert body["access_token"]
    assert "password" not in str(body["user"]).lower()


def test_password_is_stored_hashed(client):
    client.post("/api/auth/register", json=_register_body(email="hash@test.com"))
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "hash@test.com").first()
        assert user.password_hash != "Password123"
        assert user.password_hash.startswith("$2")  # bcrypt hashes start like this
    finally:
        db.close()


def test_duplicate_email_is_rejected(client):
    client.post("/api/auth/register", json=_register_body())
    response = client.post("/api/auth/register", json=_register_body())
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_wrong_password_and_unknown_email_give_the_same_error(client):
    client.post("/api/auth/register", json=_register_body())
    wrong_password = client.post(
        "/api/auth/login", json={"email": "new@test.com", "password": "WrongPass1"}
    )
    unknown_email = client.post(
        "/api/auth/login", json={"email": "nobody@test.com", "password": "Password123"}
    )
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]


def test_login_success(client):
    client.post("/api/auth/register", json=_register_body())
    response = client.post(
        "/api/auth/login", json={"email": "new@test.com", "password": "Password123"}
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_protected_route_needs_a_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code in (401, 403)


def test_invalid_token_is_rejected(client):
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_overlong_unicode_password_is_rejected_cleanly(client):
    # 40 emoji is only 40 characters but 160 bytes, which bcrypt cannot handle
    response = client.post("/api/auth/register", json=_register_body(password="😀" * 40))
    assert response.status_code == 422


def test_profile_update_and_phone_validation(client, make_user):
    user = make_user("student")
    ok = client.put(
        "/api/auth/me",
        json={"name": "Renamed User", "college": "Some College", "phone": "9123456780"},
        headers=user["headers"],
    )
    assert ok.status_code == 200
    assert ok.json()["name"] == "Renamed User"

    bad = client.put(
        "/api/auth/me",
        json={"name": "Renamed User", "college": None, "phone": "12345"},
        headers=user["headers"],
    )
    assert bad.status_code == 422


def test_student_cannot_create_an_event(client, make_user, event_payload):
    student = make_user("student")
    response = client.post("/api/events", json=event_payload(), headers=student["headers"])
    assert response.status_code == 403


def test_password_reset_flow(client, make_user):
    user = make_user("student")
    request = client.post("/api/auth/forgot-password", json={"email": user["email"]})
    assert request.status_code == 200
    code = request.json()["demo_code"]
    assert code and len(code) == 6

    wrong = "000000" if code != "000000" else "111111"
    bad = client.post("/api/auth/reset-password", json={
        "email": user["email"], "code": wrong, "new_password": "NewPass456",
    })
    assert bad.status_code == 400

    good = client.post("/api/auth/reset-password", json={
        "email": user["email"], "code": code, "new_password": "NewPass456",
    })
    assert good.status_code == 200

    new_login = client.post(
        "/api/auth/login", json={"email": user["email"], "password": "NewPass456"}
    )
    old_login = client.post(
        "/api/auth/login", json={"email": user["email"], "password": "Password123"}
    )
    assert new_login.status_code == 200
    assert old_login.status_code == 401


def test_forgot_password_does_not_reveal_unknown_emails(client):
    response = client.post("/api/auth/forgot-password", json={"email": "ghost@test.com"})
    assert response.status_code == 200
    assert response.json()["demo_code"] is None