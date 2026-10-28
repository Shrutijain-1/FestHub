"""Simulated payments and refunds. No real money is involved."""


def test_paid_event_requires_a_payment_method(client, make_user, make_event, register_for):
    organizer, student = make_user("organizer"), make_user("student")
    event = make_event(organizer, registration_fee=100)

    response = register_for(event["id"], student)  # no payment method
    assert response.status_code == 400
    assert "paid event" in response.json()["detail"].lower()

    # no seat was taken
    after = client.get(f"/api/events/{event['id']}", headers=student["headers"]).json()
    assert after["seats_available"] == after["capacity"]


def test_paid_registration_records_the_payment(client, make_user, make_event, register_for):
    organizer, student = make_user("organizer"), make_user("student")
    event = make_event(organizer, registration_fee=150)

    response = register_for(event["id"], student, payment_method="UPI")
    assert response.status_code == 201
    body = response.json()
    assert body["amount_paid"] == 150
    assert body["payment_status"] == "paid"
    assert body["payment_method"] == "UPI"
    assert body["payment_reference"].startswith("PAY-")


def test_amount_comes_from_the_event_not_the_client(client, make_user, make_event):
    organizer, student = make_user("organizer"), make_user("student")
    event = make_event(organizer, registration_fee=200)

    response = client.post(
        f"/api/events/{event['id']}/register",
        json={
            "student_name": "Test Student",
            "student_email": student["email"],
            "student_college": "Test College",
            "student_phone": "9876543210",
            "payment_method": "Card",
            "amount_paid": 1,  # a cheating attempt: it must be ignored
        },
        headers=student["headers"],
    )
    assert response.status_code == 201
    assert response.json()["amount_paid"] == 200


def test_unknown_payment_method_is_rejected(client, make_user, make_event, register_for):
    organizer, student = make_user("organizer"), make_user("student")
    event = make_event(organizer, registration_fee=100)
    response = register_for(event["id"], student, payment_method="Bitcoin")
    assert response.status_code == 422


def test_cancelling_a_paid_registration_starts_a_refund(client, make_user, make_event, register_for):
    organizer, student = make_user("organizer"), make_user("student")
    event = make_event(organizer, registration_fee=100)
    registration = register_for(event["id"], student, payment_method="Card").json()

    cancel = client.delete(f"/api/registrations/{registration['id']}", headers=student["headers"])
    assert cancel.status_code == 200
    body = cancel.json()
    assert body["status"] == "cancelled"
    assert body["payment_status"] == "refund_initiated"
    assert body["refund_reference"].startswith("RFD-")
    assert "24 hours" in body["refund_message"]
    assert "100" in body["refund_message"]


def test_cancelling_a_free_registration_has_no_refund(client, make_user, make_event, register_for):
    organizer, student = make_user("organizer"), make_user("student")
    event = make_event(organizer)  # free
    registration = register_for(event["id"], student).json()

    body = client.delete(
        f"/api/registrations/{registration['id']}", headers=student["headers"]
    ).json()
    assert body["payment_status"] == "not_required"
    assert body["refund_message"] is None


def test_registering_again_after_a_refund_needs_a_new_payment(
    client, make_user, make_event, register_for
):
    organizer, student = make_user("organizer"), make_user("student")
    event = make_event(organizer, registration_fee=100)
    first = register_for(event["id"], student, payment_method="UPI").json()
    client.delete(f"/api/registrations/{first['id']}", headers=student["headers"])

    assert register_for(event["id"], student).status_code == 400  # must pay again

    again = register_for(event["id"], student, payment_method="Card")
    assert again.status_code == 201
    body = again.json()
    assert body["id"] == first["id"]  # same database row is reused
    assert body["payment_status"] == "paid"
    assert body["payment_method"] == "Card"
    assert body["refund_reference"] is None


def test_organizer_sees_payment_details(client, make_user, make_event, register_for):
    organizer, student = make_user("organizer"), make_user("student")
    event = make_event(organizer, registration_fee=100)
    register_for(event["id"], student, payment_method="UPI")

    rows = client.get(
        f"/api/events/{event['id']}/registrations", headers=organizer["headers"]
    ).json()
    assert rows[0]["amount_paid"] == 100
    assert rows[0]["payment_status"] == "paid"
    assert rows[0]["payment_reference"].startswith("PAY-")