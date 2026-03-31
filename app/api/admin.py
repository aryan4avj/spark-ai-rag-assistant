from fastapi import APIRouter, Header, HTTPException, status

from app.core.config import settings
from app.ingestion.indexer import reindex_documents
from app.schemas.admin import ReindexResponse

router = APIRouter(prefix="/admin", tags=["admin"])


def validate_admin_api_key(admin_api_key: str | None) -> None:
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ADMIN_API_KEY is not configured.",
        )

    if admin_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key.",
        )


@router.post("/reindex", response_model=ReindexResponse)
def reindex(
    x_admin_api_key: str | None = Header(default=None),
) -> ReindexResponse:
    validate_admin_api_key(x_admin_api_key)
    result = reindex_documents()

    return ReindexResponse(
        status="ok",
        documents_indexed=result.document_count,
        chunks_indexed=result.chunk_count,
        vector_size=result.vector_size,
    )
