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

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
