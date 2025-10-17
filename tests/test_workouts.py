from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_recommendation_returns_hypertrophy_program():
    response = client.get(
        "/api/workouts/recommendations",
        params={
            "goal": "hypertrophy",
            "experience_level": "intermediate",
            "available_days": 4,
            "equipment": ["barbell", "dumbbells", "cables", "machines"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"], "Expected at least one recommendation"
    assert payload["items"][0]["goal"] == "hypertrophy"


def test_fallback_recommendation_when_equipment_is_limited():
    response = client.get(
        "/api/workouts/recommendations",
        params={
            "goal": "strength",
            "experience_level": "beginner",
            "available_days": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"], "Fallback should still produce recommendations"
    assert "No exact template fit" in payload["rationale"]
