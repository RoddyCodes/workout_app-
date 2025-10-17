from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.chat import _keywords_from_query


def test_health_endpoint_200():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json().get("status") == "ok"


def test_keywords_from_query_basic():
    # Sanity check keyword extraction helps retrieval
    q = "Who is Jeff Nippard and what are his key hypertrophy principles?"
    tokens = _keywords_from_query(q)
    # Should keep domain terms, not filler words
    assert any(t in tokens for t in ["jeff", "nippard", "hypertrophy", "principles"])  # noqa: F401
    assert all(len(t) > 2 for t in tokens)
