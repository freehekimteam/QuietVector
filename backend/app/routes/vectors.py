from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..qdrant.client import get_qdrant_client
from ..schemas.vectors import DeleteRequest, InsertVectorsRequest, SearchRequest
from ..services.vector_service import VectorService
from .deps import require_auth

router = APIRouter(prefix="/vectors", tags=["Vectors"])


async def get_vector_service(_: str = Depends(require_auth)) -> VectorService:
    """Dependency injection for VectorService"""
    client = await get_qdrant_client()
    return VectorService(client)


@router.post("/insert")
async def insert_vectors(
    body: InsertVectorsRequest,
    service: VectorService = Depends(get_vector_service)
) -> dict[str, int]:
    """Insert or update vectors in a collection"""
    try:
        return await service.insert_vectors(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to insert vectors: {str(e)}")


@router.post("/search")
async def search(
    body: SearchRequest,
    service: VectorService = Depends(get_vector_service)
) -> dict[str, list[dict[str, Any]]]:
    """Search for similar vectors"""
    try:
        return await service.search_vectors(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search failed: {str(e)}")


@router.post("/delete")
async def delete_points(
    body: DeleteRequest,
    service: VectorService = Depends(get_vector_service)
) -> dict[str, int]:
    """Delete vectors from collection"""
    try:
        return await service.delete_vectors(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete vectors: {str(e)}")

