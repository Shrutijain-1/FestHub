"""Event visibility, ownership rules, and the registration rules."""
from datetime import datetime, timedelta


def test_published_event_is_visible_to_students(client, make_user, make_event):
    organizer, student = make_user("organizer"), make_user("student")
    make_event(organizer, title="Visible Event")
    response = client.get("/api/events", headers=student["headers"])
    assert response.status_code == 200
    assert [e["title"] for e in response.json()] == ["Visible Event"]


def test_draft_event_is_hidden_from_students(client, make_user, make_event):
    organizer, student = make_user("organizer"), make_user("student")
    event = make_event(organizer, status="draft")

    listing = client.get("/api/events", headers=student["headers"])
    assert listing.json() == []
    details = client.get(f"/api/events/{event['id']}", headers=student["headers"])
    assert details.status_code == 404
    # The owner can still see their own draft
    owner_view = client.get(f"/api/events/{event['id']}", headers=organizer["headers"])
    assert owner_view.status_code == 200


def test_only_the_owner_can_edit_or_delete(client, make_user, make_event, event_payload):
    owner, other = make_user("organizer"), make_user("organizer")
    event = make_event(owner)

    edit = client.put(
        f"/api/events/{event['id']}", json=event_payload(title="Hacked"), headers=other["headers"]
    )
    assert edit.status_code == 403
    delete = client.delete(f"/api/events/{event['id']}", headers=other["headers"])
    assert delete.status_code == 403

    owner_delete = client.delete(f"/api/events/{event['id']}", headers=owner["headers"])
    assert owner_delete.status_code == 204
    gone = client.get(f"/api/events/{event['id']}", headers=owner["headers"])
    assert gone.status_code == 404


def test_search_and_filters(client, make_user, make_event):
    organizer, student = make_user("organizer"), make_user("student")
    make_event(organizer, title="Python Bootcamp", event_type="Workshop", registration_fee=100)
    make_event(organizer, title="Dance Night", event_type="Cultural", registration_fee=0)

    def titles(**params):
        response = client.get("/api/events", params=params, headers=student["headers"])
        assert response.status_code == 200
        return sorted(e["title"] for e in response.json())

    assert titles() == ["Dance Night", "Python Bootcamp"]
    assert titles(q="python") == ["Python Bootcamp"]
    assert titles(event_type="Cultural") == ["Dance Night"]
    assert titles(fee="paid") == ["Python Bootcamp"]
    assert titles(fee="free") == ["Dance Night"]
    assert titles(city="Pune") == ["Dance Night", "Python Bootcamp"]
    assert titles(city="Mumbai") == []


def test_duplicate_registration_is_rejected(client, make_user, make_event, register_for):
    organizer, student = make_user("organizer"), make_user("student")
    event = make_event(organizer)

    assert register_for(event["id"], student).status_code == 201
    again = register_for(event["id"], student)
    assert again.status_code == 409
    assert "already registered" in again.json()["detail"].lower()


def test_full_event_rejects_new_registrations(client, make_user, make_event, register_for):
    organizer = make_user("organizer")
    first, second = make_user("student"), make_user("student")
    event = make_event(organizer, capacity=1)

    assert register_for(event["id"], first).status_code == 201
    response = register_for(event["id"], second)
    assert response.status_code == 409
    assert "full" in response.json()["detail"].lower()


def test_cancelling_frees_the_seat_and_reuses_the_row(client, make_user, make_event, register_for):
    organizer, student = make_user("organizer"), make_user("student")
    event = make_event(organizer, capacity=5)

    registration = register_for(event["id"], student).json()
    after_register = client.get(f"/api/events/{event['id']}", headers=student["headers"]).json()
    assert after_register["seats_available"] == 4

    cancel = client.delete(f"/api/registrations/{registration['id']}", headers=student["headers"])
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"
    after_cancel = client.get(f"/api/events/{event['id']}", headers=student["headers"]).json()
    assert after_cancel["seats_available"] == 5

    again = register_for(event["id"], student)
    assert again.status_code == 201
    assert again.json()["id"] == registration["id"]  # same database row


def test_student_cannot_cancel_someone_elses_registration(client, make_user, make_event, register_for):
    organizer = make_user("organizer")
    owner, intruder = make_user("student"), make_user("student")
    event = make_event(organizer)
    registration = register_for(event["id"], owner).json()

    response = client.delete(f"/api/registrations/{registration['id']}", headers=intruder["headers"])
    assert response.status_code == 403


def test_registration_after_the_deadline_is_rejected(client, make_user, make_event, register_for):
    organizer, student = make_user("organizer"), make_user("student")
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    event = make_event(organizer, registration_deadline=yesterday)

    response = register_for(event["id"], student)
    assert response.status_code == 400
    assert "closed" in response.json()["detail"].lower()


def test_organizer_cannot_register_for_events(client, make_user, make_event, register_for):
    organizer = make_user("organizer")
    event = make_event(organizer)
    assert register_for(event["id"], organizer).status_code == 403


def test_attendee_list_is_for_the_owner_only(client, make_user, make_event, register_for):
    owner, other = make_user("organizer"), make_user("organizer")
    student = make_user("student")
    event = make_event(owner)
    register_for(event["id"], student)

    blocked = client.get(f"/api/events/{event['id']}/registrations", headers=other["headers"])
    assert blocked.status_code == 403
    allowed = client.get(f"/api/events/{event['id']}/registrations", headers=owner["headers"])
    assert allowed.status_code == 200
    assert len(allowed.json()) == 1


def test_capacity_cannot_drop_below_registered_students(
    client, make_user, make_event, register_for, event_payload
):
    organizer = make_user("organizer")
    event = make_event(organizer, capacity=5)
    register_for(event["id"], make_user("student"))
    register_for(event["id"], make_user("student"))

    response = client.put(
        f"/api/events/{event['id']}", json=event_payload(capacity=1), headers=organizer["headers"]
    )
    assert response.status_code == 400
    assert "capacity" in response.json()["detail"].lower()


def test_fake_image_is_rejected(client, make_user, make_event):
    organizer = make_user("organizer")
    event = make_event(organizer)
    response = client.post(
        f"/api/events/{event['id']}/image",
        files={"file": ("fake.png", b"this is not an image", "image/png")},
        headers=organizer["headers"],
    )
    assert response.status_code == 400
    assert "valid" in response.json()["detail"].lower()