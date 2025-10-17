from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    # Basic identifiers and context
    session_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    goal: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    experience_level: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    # Feedback metrics
    rpe: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    adherence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    goal: Mapped[str] = mapped_column(String(64), index=True)
    experience_level: Mapped[str] = mapped_column(String(32), index=True)
    # Store the entire template as JSON string for simplicity on SQLite
    payload: Mapped[str] = mapped_column(Text, nullable=False)


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    content: Mapped[str] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
