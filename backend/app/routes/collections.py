from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from qdrant_client.models import Distance as QDistance, VectorParams

from ..qdrant.client import get_qdrant_client
from ..schemas.collections import CollectionInfo, CreateCollectionRequest
from .deps import require_auth

router = APIRouter(prefix="/collections", tags=["Collections"])


def _map_distance(name: str) -> QDistance:
    n = name.lower()
    if n.startswith("cos"):
        return QDistance.COSINE
    if n.startswith("dot"):
        return QDistance.DOT
    return QDistance.EUCLID


@router.get("", response_model=List[CollectionInfo])
def list_collections(_: str = Depends(require_auth)) -> list[CollectionInfo]:
    c = get_qdrant_client()
    cols = c.get_collections().collections
    out: list[CollectionInfo] = []
    for col in cols:
        info = c.get_collection(col.name)
        out.append(
            CollectionInfo(
                name=col.name,
                points_count=getattr(info, "points_count", 0) or 0,
                vectors_count=getattr(info, "vectors_count", 0) or 0,
                status=getattr(getattr(info, "status", None), "value", str(getattr(info, "status", "unknown"))),
            )
        )
    return out


@router.get("/{name}", response_model=CollectionInfo)
def get_collection(name: str, _: str = Depends(require_auth)) -> CollectionInfo:
    c = get_qdrant_client()
    try:
        info = c.get_collection(name)
    except Exception:
        raise HTTPException(status_code=404, detail="Collection not found")
    return CollectionInfo(
        name=name,
        points_count=getattr(info, "points_count", 0) or 0,
        vectors_count=getattr(info, "vectors_count", 0) or 0,
        status=getattr(getattr(info, "status", None), "value", str(getattr(info, "status", "unknown"))),
    )


@router.post("", status_code=201)
def create_collection(body: CreateCollectionRequest, _: str = Depends(require_auth)) -> dict:
    c = get_qdrant_client()
    vectors = VectorParams(size=body.vectors_size, distance=_map_distance(body.distance))
    try:
        c.create_collection(collection_name=body.name, vectors_config=vectors, hnsw_config=None)
    except Exception as e:
        # If exists -> try no-op error mapping
        raise HTTPException(status_code=400, detail=str(e))
    return {"created": body.name}


@router.delete("/{name}")
def delete_collection(name: str, _: str = Depends(require_auth)) -> dict:
    c = get_qdrant_client()
    try:
        c.delete_collection(name)
        return {"deleted": name}
    except Exception:
        raise HTTPException(status_code=404, detail="Collection not found")

