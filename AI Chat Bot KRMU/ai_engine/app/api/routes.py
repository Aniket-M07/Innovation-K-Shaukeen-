from functools import lru_cache

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import EmbedResponse, QueryRequest, QueryResponse
from app.services.rag_service import RAGService

router = APIRouter()


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    return RAGService()


@router.post("/embed", response_model=EmbedResponse)
async def embed_documents(files: list[UploadFile] = File(...)) -> EmbedResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    try:
        return await get_rag_service().embed_files(files)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to embed documents: {error}") from error


@router.post("/query", response_model=QueryResponse)
async def query_documents(payload: QueryRequest) -> QueryResponse:
    try:
        return get_rag_service().query(payload.query, payload.top_k, payload.feedback_context)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {error}") from error