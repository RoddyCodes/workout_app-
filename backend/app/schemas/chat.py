from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatSource(BaseModel):
    title: str
    url: Optional[str] = None
    score: Optional[float] = Field(default=None, description="Similarity or match score")


class ChatRequest(BaseModel):
    message: str
    top_k: int = Field(default=3, ge=1, le=10)


class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource] = []
    model: Optional[str] = None
