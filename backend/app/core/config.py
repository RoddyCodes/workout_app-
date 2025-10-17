from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="Workout App API")
    version: str = Field(default="0.1.0")
    data_path: Path = Field(
        default=Path(__file__).resolve().parent.parent / "data" / "workouts.json"
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Allowed CORS origins for browsers",
    )
    database_url: str = Field(
        default="sqlite:///./workout.db",
        description="SQLAlchemy database URL",
    )
    llm_base_url: str = Field(
        default="http://localhost:11434/api/generate",
        description="Base URL for the local LLM API (Ollama)",
    )
    llm_model: str = Field(
        default="llama3.2:3b",
        description="Model name for the local LLM",
    )
    llm_enabled: bool = Field(default=True, description="Enable/disable LLM calls")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
