from functools import lru_cache
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query

from backend.app.schemas.workout import RecommendationRequest, RecommendationResponse
from backend.app.services.recommendation import WorkoutRecommender

router = APIRouter(prefix="/workouts", tags=["Workouts"])


@lru_cache
def get_recommender() -> WorkoutRecommender:
    """Provide a cached recommender instance."""
    return WorkoutRecommender()


GoalParam = Annotated[str, Query(..., min_length=3, description="Primary training goal.")]
ExperienceParam = Annotated[
    str,
    Query(
        ...,
        min_length=3,
        description="Client experience level (beginner/intermediate/advanced).",
    ),
]
DaysParam = Annotated[
    int,
    Query(
        ...,
        ge=2,
        le=7,
        description="Training days available per week.",
    ),
]
EquipmentParam = Annotated[
    List[str] | None,
    Query(description="Available equipment, repeated per item."),
]
RecommenderDep = Annotated[WorkoutRecommender, Depends(get_recommender)]


@router.get("/recommendations", response_model=RecommendationResponse)
async def recommend_workouts(
    goal: GoalParam,
    experience_level: ExperienceParam,
    available_days: DaysParam,
    recommender: RecommenderDep,
    equipment: EquipmentParam = None,
) -> RecommendationResponse:
    """Return science-based workout templates that align with the request."""
    request_payload = RecommendationRequest(
        goal=goal,
        experience_level=experience_level,
        available_days=available_days,
        equipment=equipment or [],
    )
    return recommender.recommend(request_payload)
