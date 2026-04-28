from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.admin import router as admin_router
from app.api.agent import router as agent_router
from app.api.health import router as health_router
from app.api.query import router as query_router
from app.core.config import settings

FRONTEND_INDEX = Path(__file__).resolve().parents[1] / "frontend" / "index.html"

app = FastAPI(
    title="Spark AI RAG Assistant",
    version="0.1.0",
)

app.include_router(admin_router)
app.include_router(agent_router)
app.include_router(health_router)
app.include_router(query_router)


@app.get("/")
def root() -> FileResponse:
    return FileResponse(FRONTEND_INDEX)
