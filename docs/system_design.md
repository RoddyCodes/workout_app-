# System Design Overview

This document outlines the high-level design for the Workout App platform, starting with workout recommendations and expanding toward nutrition guidance.

## Vision
- Deliver evidence-based workouts influenced by Jeff Nippard's programming philosophy.
- Support progressive overload, balanced volume, and recovery-aware planning.
- Grow into a personalised coaching assistant that also surfaces macro-conscious recipes.

## Current Scope (MVP)
- FastAPI backend serving REST endpoints under `/api`.
- In-memory template catalogue sourced from `backend/app/data/workouts.json`.
- Heuristic recommender scores templates by goal, experience, frequency, and equipment coverage.
- Automated tests ensure the recommendation endpoint returns sensible payloads and fallbacks.

## Domain Model
- **WorkoutTemplate**: Describes a mesocycle-ready training plan with session breakdowns.
- **TrainingSession**: Encapsulates focus, compound lifts, and accessory work for a specific day.
- **RecommendationRequest**: Inputs from user (goal, experience, weekly availability, equipment).
- **RecommendationResponse**: Ranked list of templates plus rationale for transparency.

## API Plan
1. `GET /api/workouts/recommendations` (implemented) – Accepts query params, returns templates.
2. `POST /api/workouts/feedback` (planned) – Collects subjective effort and progress markers.
3. `GET /api/recipes/recommendations` (future) – Serves macro-aligned recipes once data model is ready.

## Data Strategy
- Short term: Curated JSON templates derived from coaching expertise.
- Mid term: Store workouts, user preferences, and session logs in PostgreSQL (SQLAlchemy + Alembic).
- Long term: Feature store for ML-driven personalisation incorporating session RPE, recovery, and adherence data.

## Machine Learning Roadmap
1. Add rules-based adjustments (e.g., increase volume when RPE < target for two weeks).
2. Train regression model to predict strength progression and auto-tune load prescriptions.
3. Integrate recommendation system blending collaborative filtering (community data) with content features.

## Nutrition Module Concept
- Recipe data points: macros, micro highlights, prep time, cuisine, dietary tags.
- Recommendation inputs: caloric target, macro ratios, cooking skill, prep time constraints.
- Output: Daily or weekly meal plans with shopping list generation.

## Deployment Considerations
- Containerise API using Docker with multi-stage build.
- Use Gunicorn/Uvicorn workers behind an ASGI server for production.
- Configure CI to run test suite, linting, and static analysis.
- Add observability hooks (structured logging, request metrics) before public launch.

## Next Expansions
- User authentication and profile management.
- Habit tracking integration (steps, sleep) pulled from wearable APIs via background jobs.
- Frontend client (React/Next.js) to visualise programming blocks and recipe plans.
