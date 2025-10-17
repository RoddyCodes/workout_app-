from fastapi import FastAPI

from backend.app.api.routes.workouts import router as workouts_router
from backend.app.core.config import settings


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
    app.include_router(workouts_router, prefix="/api")
    return app


app = create_application()


@app.get("/health", tags=["Health"])
async def healthcheck() -> dict[str, str]:
    """Expose a basic readiness probe."""
    return {"status": "ok"}
