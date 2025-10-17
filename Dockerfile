# syntax=docker/dockerfile:1.7-labs

FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# Install system deps (build for uvicorn[standard] optional wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - --version 2.2.1 \
  && ln -s $HOME/.local/bin/poetry /usr/local/bin/poetry

# Copy project files
COPY pyproject.toml README.md /app/
COPY backend /app/backend

# Install dependencies (no venv inside container)
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi --no-root

EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
