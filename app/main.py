from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.query import router as query_router
from app.core.config import settings

app = FastAPI(
    title="Spark AI RAG Assistant",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(query_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Spark AI RAG Assistant API",
        "environment": settings.app_env,
    }
