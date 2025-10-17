from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_create_feedback_minimal_payload():
    res = client.post(
        "/api/feedback/",
        json={
            "session_id": "S1",
            "rpe": 8,
            "adherence": 90,
            "notes": "Felt strong today",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "id" in data


def test_create_feedback_validation():
    # adherence out of range
    res = client.post(
        "/api/feedback/",
        json={
            "adherence": 150,
        },
    )
    assert res.status_code == 422
