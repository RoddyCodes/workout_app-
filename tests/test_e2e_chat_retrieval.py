from __future__ import annotations

from contextlib import contextmanager

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings
from backend.app.db.models import KnowledgeItem
from backend.app.db.session import Base, get_session
from backend.app.main import app


@contextmanager
def override_db():
    # Use isolated on-disk SQLite to allow multiple connections
    engine = create_engine("sqlite:///./test_chat.db", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def _get_session():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_session] = _get_session
    try:
        yield TestingSessionLocal
    finally:
        app.dependency_overrides.pop(get_session, None)


def test_chat_returns_sources_with_seeded_docs(tmp_path):
    # Disable LLM to avoid network calls; force retrieval-only friendly summary
    prev = settings.llm_enabled
    settings.llm_enabled = False
    try:
        with override_db() as Sess:
            with Sess() as s:
                s.add(
                    KnowledgeItem(
                        title="Jeff Nippard – Profile (test)",
                        content=(
                            "Jeff Nippard is a natural bodybuilder and educator focusing on "
                            "evidence-based training."
                        ),
                        source_url="https://www.youtube.com/@JeffNippard",
                        tags="jeff nippard,hypertrophy,education",
                    )
                )
                s.add(
                    KnowledgeItem(
                        title="Hypertrophy Principles – Volume & Progression",
                        content=(
                            "Key hypertrophy drivers include mechanical tension, "
                            "sufficient volume, progressive overload, "
                            "and recovery."
                        ),
                        source_url="internal:test",
                        tags="hypertrophy,principles",
                    )
                )
                s.commit()

            client = TestClient(app)
            payload = {
                "message": "Who is Jeff Nippard and what are his key hypertrophy principles?",
                "top_k": 3,
            }
            res = client.post("/api/chat/", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert isinstance(data["answer"], str) and len(data["answer"]) > 0
            # Should include at least one source due to retrieval success
            assert len(data["sources"]) >= 1
    finally:
        settings.llm_enabled = prev
