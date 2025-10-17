from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app


def test_chat_endpoint_fallback_returns_answer_and_sources():
    client = TestClient(app)
    payload = {"message": "How many days should I train for hypertrophy?", "top_k": 2}
    res = client.post("/api/chat/", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data["answer"], str) and len(data["answer"]) > 0
    assert isinstance(data["sources"], list)