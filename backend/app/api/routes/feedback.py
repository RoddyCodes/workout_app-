from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.models import Feedback
from backend.app.db.session import get_session
from backend.app.schemas.feedback import FeedbackCreate, FeedbackOut

router = APIRouter(prefix="/feedback", tags=["Feedback"])


SessionDep = Annotated[Session, Depends(get_session)]


@router.post("/", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def create_feedback(
    payload: FeedbackCreate,
    session: SessionDep,
) -> FeedbackOut:
    try:
        entity = Feedback(
            session_id=payload.session_id,
            goal=payload.goal,
            experience_level=payload.experience_level,
            rpe=payload.rpe,
            adherence=payload.adherence,
            notes=payload.notes,
        )
        session.add(entity)
        session.commit()
        session.refresh(entity)
        return FeedbackOut.model_validate(entity)
    except Exception as exc:  # pragma: no cover
        session.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
