# Simple dev workflow

.PHONY: dev up api db-migrate db-seed test lint clean

VENV=.venv
PY=$(VENV)/bin/python
PIP=$(VENV)/bin/pip

$(VENV)/bin/activate:
	python -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -e .

up: $(VENV)/bin/activate db-migrate db-seed
	$(VENV)/bin/uvicorn backend.app.main:app --reload

api: $(VENV)/bin/activate
	$(VENV)/bin/uvicorn backend.app.main:app --reload

db-migrate: $(VENV)/bin/activate
	$(VENV)/bin/alembic upgrade head

db-seed: $(VENV)/bin/activate
	$(PY) scripts/seed_workouts.py

test: $(VENV)/bin/activate
	$(VENV)/bin/pytest -q

lint: $(VENV)/bin/activate
	$(VENV)/bin/ruff check --quiet

clean:
	rm -rf $(VENV) *.db .coverage* .pytest_cache .ruff_cache htmlcov
