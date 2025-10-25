from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..qdrant.client import get_qdrant_client
from ..schemas.collections import CollectionInfo, CreateCollectionRequest
from ..services.collection_service import CollectionService
from .deps import require_auth

router = APIRouter(prefix="/collections", tags=["Collections"])


async def get_collection_service(_: str = Depends(require_auth)) -> CollectionService:
    """Dependency injection for CollectionService"""
    client = await get_qdrant_client()
    return CollectionService(client)


@router.get("")
async def list_collections(
    service: CollectionService = Depends(get_collection_service)
) -> dict[str, list[dict[str, Any]]]:
    """List all collections"""
    collections = await service.list_collections()
    return {"collections": collections}


@router.get("/{name}", response_model=CollectionInfo)
async def get_collection(
    name: str,
    service: CollectionService = Depends(get_collection_service)
) -> CollectionInfo:
    """Get detailed collection information"""
    try:
        return await service.get_collection_info(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Collection not found: {str(e)}")


@router.post("", status_code=201)
async def create_collection(
    body: CreateCollectionRequest,
    service: CollectionService = Depends(get_collection_service)
) -> dict[str, Any]:
    """Create a new collection"""
    try:
        return await service.create_collection(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create collection: {str(e)}")


@router.delete("/{name}")
async def delete_collection(
    name: str,
    service: CollectionService = Depends(get_collection_service)
) -> dict[str, bool]:
    """Delete a collection"""
    try:
        return await service.delete_collection(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Collection not found: {str(e)}")

