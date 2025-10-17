from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    session_id: Optional[str] = Field(default=None, max_length=64)
    goal: Optional[str] = Field(default=None, max_length=64)
    experience_level: Optional[str] = Field(default=None, max_length=32)
    rpe: Optional[int] = Field(default=None, ge=1, le=10, description="Session RPE 1-10")
    adherence: Optional[int] = Field(
        default=None, ge=0, le=100, description="Percent adherence to planned work"
    )
    notes: Optional[str] = Field(default=None, max_length=2000)


class FeedbackOut(BaseModel):
    id: int

    model_config = {
        "from_attributes": True,
    }
