"""AI access rules. No real Gemini calls are made (the key is empty in tests)."""

BODY = {"title": "AI Workshop", "audience": "Students"}


def test_student_cannot_use_organizer_ai_tools(client, make_user):
    student = make_user("student")
    response = client.post("/api/ai/generate-description", json=BODY, headers=student["headers"])
    assert response.status_code == 403


def test_missing_api_key_gives_a_friendly_error(client, make_user):
    organizer = make_user("organizer")
    response = client.post("/api/ai/generate-description", json=BODY, headers=organizer["headers"])
    assert response.status_code == 503
    assert "not set up" in response.json()["detail"]