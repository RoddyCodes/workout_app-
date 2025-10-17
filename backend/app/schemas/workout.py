from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class TrainingSession(BaseModel):
    day: str = Field(..., description="Weekday identifier or session number.")
    focus: str = Field(..., description="Primary emphasis of the session.")
    primary_lifts: List[str] = Field(
        default_factory=list, description="Key multi-joint lifts to progress."
    )
    accessory_work: List[str] = Field(
        default_factory=list, description="Support work to balance the session."
    )


class WorkoutTemplate(BaseModel):
    id: str = Field(..., description="Stable identifier for the template.")
    name: str
    description: str
    goal: str
    experience_level: str = Field(..., description="Skill level the template is designed for.")
    weekly_frequency_options: List[int] = Field(
        ..., description="Supported training day counts per week."
    )
    equipment: List[str] = Field(
        default_factory=list, description="Equipment assumed by the template."
    )
    training_split: List[TrainingSession]
    coaching_notes: List[str] = Field(
        default_factory=list, description="Practical notes derived from evidence-based coaching."
    )


class RecommendationRequest(BaseModel):
    goal: str = Field(..., min_length=3)
    experience_level: str = Field(..., min_length=3)
    available_days: int = Field(..., ge=2, le=7)
    equipment: List[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    items: List[WorkoutTemplate]
    rationale: str
