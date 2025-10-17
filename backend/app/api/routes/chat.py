from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_session
from backend.app.schemas.chat import ChatRequest, ChatResponse
from backend.app.services.chat import chat as chat_service

router = APIRouter(prefix="/chat", tags=["chat"])

SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, session: SessionDep) -> ChatResponse:
    return await chat_service(session, payload.message, top_k=payload.top_k)
