from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.feedback import router as feedback_router
from backend.app.api.routes.workouts import router as workouts_router
from backend.app.core.config import settings
from backend.app.db.session import Base, engine


def create_application() -> FastAPI:
    """Construct the FastAPI application with configured routes."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        summary="Science-based workout recommendations",
        description=(
            "API that delivers resistance training programs inspired by Jeff "
            "Nippard's evidence-based principles."
        ),
    )
    # CORS for frontend clients
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(workouts_router, prefix="/api")
    app.include_router(feedback_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    return app


app = create_application()

# Create tables on startup (swap to Alembic later)
Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["Health"])
async def healthcheck() -> dict[str, str]:
    """Expose a basic readiness probe."""
    return {"status": "ok"}
