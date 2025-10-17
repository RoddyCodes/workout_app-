from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from backend.app.core.config import settings
from backend.app.schemas.workout import (
    RecommendationRequest,
    RecommendationResponse,
    WorkoutTemplate,
)

_EXPERIENCE_RANK = {
    "beginner": 0,
    "novice": 0,
    "intermediate": 1,
    "advanced": 2,
}


@dataclass
class RankedTemplate:
    template: WorkoutTemplate
    score: float


class WorkoutRecommender:
    """Recommend workout templates based on simple heuristic ranking."""

    def __init__(self, data_path: Path | None = None) -> None:
        self.data_path = data_path or settings.data_path
        self._templates = self._load_templates(self.data_path)

    @staticmethod
    def _load_templates(source: Path) -> List[WorkoutTemplate]:
        if not source.exists():
            raise FileNotFoundError(f"Workout template source not found: {source}")

        with source.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        templates: List[WorkoutTemplate] = []
        for raw_template in payload.get("templates", []):
            templates.append(WorkoutTemplate.model_validate(raw_template))
        return templates

    def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        primary_matches = [
            template
            for template in self._templates
            if self._is_goal_match(template, request)
            and self._is_experience_match(template, request)
            and self._is_frequency_match(template, request)
            and self._is_equipment_match(template, request)
        ]

        if primary_matches:
            rationale = (
                f"Identified {len(primary_matches)} template(s) aligned with goal "
                f"'{request.goal}' and {request.available_days} weekly sessions."
            )
            return RecommendationResponse(items=primary_matches[:3], rationale=rationale)

        ranked = self._rank_templates(request)
        fallback_templates = [item.template for item in ranked[:3]]
        rationale = (
            "No exact template fit. Returning closest options based on frequency, "
            "equipment coverage, and experience similarity."
        )
        return RecommendationResponse(items=fallback_templates, rationale=rationale)

    def _rank_templates(self, request: RecommendationRequest) -> List[RankedTemplate]:
        ranked: List[RankedTemplate] = []
        for template in self._templates:
            freq_gap = self._frequency_gap(template, request)
            equip_score = self._equipment_overlap(template, request)
            experience_gap = abs(
                self._experience_rank(template.experience_level)
                - self._experience_rank(request.experience_level)
            )
            score = (
                (1.0 - freq_gap) * 0.5
                + equip_score * 0.35
                + (1.0 - experience_gap * 0.4) * 0.15
            )
            ranked.append(RankedTemplate(template=template, score=score))

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked

    @staticmethod
    def _is_goal_match(
        template: WorkoutTemplate, request: RecommendationRequest
    ) -> bool:
        request_goal = request.goal.lower()
        template_goal = template.goal.lower()
        return request_goal in template_goal or template_goal in request_goal

    def _is_experience_match(
        self, template: WorkoutTemplate, request: RecommendationRequest
    ) -> bool:
        template_rank = self._experience_rank(template.experience_level)
        request_rank = self._experience_rank(request.experience_level)
        return template_rank <= request_rank

    @staticmethod
    def _is_frequency_match(
        template: WorkoutTemplate, request: RecommendationRequest
    ) -> bool:
        return request.available_days in template.weekly_frequency_options

    def _is_equipment_match(
        self, template: WorkoutTemplate, request: RecommendationRequest
    ) -> bool:
        if not template.equipment:
            return True

        if not request.equipment:
            return False

        overlap_ratio = self._equipment_overlap(template, request)
        return overlap_ratio >= 0.6

    @staticmethod
    def _experience_rank(label: str) -> int:
        return _EXPERIENCE_RANK.get(label.lower(), 1)

    @staticmethod
    def _frequency_gap(template: WorkoutTemplate, request: RecommendationRequest) -> float:
        best_gap = min(
            abs(freq - request.available_days) for freq in template.weekly_frequency_options
        )
        return min(best_gap / 4.0, 1.0)

    @staticmethod
    def _equipment_overlap(template: WorkoutTemplate, request: RecommendationRequest) -> float:
        template_equipment = {item.lower() for item in template.equipment}
        available_equipment = {item.lower() for item in request.equipment}
        if not template_equipment:
            return 1.0
        if not available_equipment:
            return 0.0
        overlap = template_equipment & available_equipment
        return len(overlap) / len(template_equipment)
