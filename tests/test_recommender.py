from __future__ import annotations

import json
from pathlib import Path

from backend.app.core.config import settings
from backend.app.schemas.workout import RecommendationRequest
from backend.app.services.recommendation import WorkoutRecommender


def test_exact_match_returns_top_template(tmp_path: Path):
    # Use real dataset
    recommender = WorkoutRecommender(data_path=settings.data_path)
    req = RecommendationRequest(
        goal="hypertrophy",
        experience_level="intermediate",
        available_days=4,
        equipment=["barbell", "dumbbells", "cables", "machines"],
    )
    res = recommender.recommend(req)
    assert res.items, "Expected at least one recommendation"
    assert res.items[0].goal == "hypertrophy"


def test_equipment_limited_triggers_fallback(tmp_path: Path):
    recommender = WorkoutRecommender(data_path=settings.data_path)
    req = RecommendationRequest(
        goal="strength",
        experience_level="beginner",
        available_days=3,
        equipment=[],
    )
    res = recommender.recommend(req)
    assert res.items, "Expected fallback recommendations"
    assert "No exact template fit" in res.rationale


essentials_json = {
    "templates": [
        {
            "id": "adv_strength",
            "name": "Advanced Strength",
            "description": "",
            "goal": "strength",
            "experience_level": "advanced",
            "weekly_frequency_options": [4],
            "equipment": ["barbell"],
            "training_split": [],
            "coaching_notes": [],
        },
        {
            "id": "beg_gains",
            "name": "Beginner Gains",
            "description": "",
            "goal": "strength",
            "experience_level": "beginner",
            "weekly_frequency_options": [3],
            "equipment": ["dumbbells"],
            "training_split": [],
            "coaching_notes": [],
        },
    ]
}


def test_experience_gating_prefers_lower_complexity(tmp_path: Path):
    data_path = tmp_path / "workouts.json"
    data_path.write_text(json.dumps(essentials_json), encoding="utf-8")

    recommender = WorkoutRecommender(data_path=data_path)
    req = RecommendationRequest(
        goal="strength",
        experience_level="beginner",
        available_days=3,
        equipment=["dumbbells", "barbell"],
    )
    res = recommender.recommend(req)
    assert res.items, "Expected recommendations for beginner"
    # Ensure beginner template surfaces ahead of advanced
    ids = [t.id for t in res.items]
    assert ids[0] == "beg_gains"
