from fastapi import FastAPI

from app.api.health import router as health_router

app = FastAPI(title="Spark AI RAG Assistant")

app.include_router(health_router)
