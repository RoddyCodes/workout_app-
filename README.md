# Workout App API

Science-first workout recommendation service that follows Jeff Nippard inspired programming principles. The project starts with evidence-based workout templates and will later expand into nutrition and recipe guidance.

## Features
- FastAPI backend serving workout recommendations via REST.
- Templates tagged by goal, experience, frequency, and equipment needs.
- Simple heuristic recommender with graceful fallbacks when inputs do not fully match.
- Pytest suite covering the recommendation endpoint.

## Getting Started
1. Install Poetry if you do not already have it (`pip install poetry`).
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Activate the virtual environment:
   ```bash
   poetry shell
   ```
4. Run the FastAPI server:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
5. Visit the automatic docs at `http://127.0.0.1:8000/docs` to explore the API.

## Running Tests
```bash
poetry run pytest
```

## Architecture
- `backend/app/main.py` boots the FastAPI instance and wires routes.
- `backend/app/api/routes/workouts.py` exposes the `/api/workouts/recommendations` endpoint.
- `backend/app/services/recommendation.py` loads templates, scores matches, and returns responses.
- `backend/app/schemas/workout.py` defines Pydantic request/response models and training session schema.
- `backend/app/data/workouts.json` stores Jeff Nippard inspired templates written in original wording.
- `tests/test_workouts.py` validates that the recommendation endpoint behaves as expected.

## Data and Assumptions
- Workouts emphasise progressive overload, volume management, and recovery aligned with evidence-based coaching literature.
- Equipment matching requires roughly 60 percent overlap to qualify as a direct match; otherwise a ranked fallback is used.
- Experience levels grant access to templates designed for the same or lower complexity.

## Roadmap
1. Add user profile persistence with relational storage (PostgreSQL or SQLite to start).
2. Layer in workout progression tracking and auto-deload suggestions.
3. Integrate nutrition and recipe recommendations with macro-aware meal planning.
4. Introduce machine learning models for personalised adjustments once usage data accumulates.

## Next Steps
- Decide on the deployment target (container, managed hosting) and produce the necessary infrastructure.
- Expand the template catalogue and begin mapping parameterised variations (goal phases, mesocycles).
- Plan the nutrition module: data model, recipe sourcing, and macro calculation engine.
