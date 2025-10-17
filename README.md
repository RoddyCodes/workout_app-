# Workout App API

Science-first workout recommendation service that follows Jeff Nippard inspired programming principles. The project starts with evidence-based workout templates and will later expand into nutrition and recipe guidance.

## Features
- FastAPI backend serving workout recommendations via REST.
- Templates tagged by goal, experience, frequency, and equipment needs.
- Simple heuristic recommender with graceful fallbacks when inputs do not fully match.
- SQLAlchemy models with a feedback endpoint and Alembic migrations.
- Pytest suite covering endpoints and service logic.
 - New: Chat endpoint backed by a local LLM (Ollama) with retrieval from the DB.

## Getting Started
1. Create and activate a venv (or use Poetry if you prefer). Using venv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -U pip
   pip install -e .
   ```
2. Run database migrations and seed templates (first run):
   ```bash
   alembic upgrade head
   python scripts/seed_workouts.py
   ```
3. Start the API:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
4. Visit `http://127.0.0.1:8000/docs` to explore the API.

## Running Tests
```bash
pytest -q
```

## Chat (MVP)
 Endpoint: `POST /api/chat/`
  - Request: `{ "message": "string", "top_k": 3 }`
  - Response: `{ "answer": "string", "sources": [{"title": "...", "url": "..."}], "model": "llama3.2:3b" }`
  - Retrieval: SQLite FTS5 + LIKE fallback. We tokenize your question to improve matches.
  - LLM: Defaults to a local Ollama server. If unreachable, you still get a concise retrieval-only answer with sources.
  - Install Ollama and run a model:
    ```bash
    brew install ollama
    ollama serve &
    ollama pull llama3.2:3b
    ollama run llama3.2:3b
    ```
  - Config: either set env vars or edit `.env` (already created):
    ```bash
    export LLM_BASE_URL=http://127.0.0.1:11434/api/generate
    export LLM_MODEL=llama3.2:3b
    export LLM_ENABLED=true
    ```

## Architecture

## Data and Assumptions

## Roadmap
1. Add user profile persistence with relational storage (PostgreSQL or SQLite to start).
2. Layer in workout progression tracking and auto-deload suggestions.
3. Integrate nutrition and recipe recommendations with macro-aware meal planning.
4. Introduce machine learning models for personalised adjustments once usage data accumulates.

## Configuration
- DATABASE_URL: Override the default SQLite dev DB. Example:
   - `export DATABASE_URL=sqlite:///./workout.db`
   - `export DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/workout`
- LLM settings:
   - `LLM_BASE_URL` (default `http://127.0.0.1:11434/api/generate`)
   - `LLM_MODEL` (default `llama3.2:3b`)
   - `LLM_ENABLED` (default `true`)

## VS Code Tasks
- API: run (reload)
- Tests: run
- DB Migrate (alembic upgrade head)
- DB Seed Workouts
 
## Notes on sources
- Keep this MVP grounded in your curated, science-based content. For Jeff Nippard YouTube material, store titles/links and (if permitted) short transcript snippets for context. The assistant references your stored context with simple citations like [1], [2].

## Next Steps
- Decide on the deployment target (container, managed hosting) and produce the necessary infrastructure.
- Expand the template catalogue and begin mapping parameterised variations (goal phases, mesocycles).
- Plan the nutrition module: data model, recipe sourcing, and macro calculation engine.
