from __future__ import annotations

from fastapi import APIRouter, Depends

from ..qdrant.client import get_qdrant_client
from .deps import require_auth

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("")
def stats(_: str = Depends(require_auth)) -> dict:
    c = get_qdrant_client()
    cols = c.get_collections().collections
    total_points = 0
    items: list[dict] = []
    for col in cols:
        info = c.get_collection(col.name)
        points = getattr(info, "points_count", 0) or 0
        vectors = getattr(info, "vectors_count", 0) or 0
        items.append({"name": col.name, "points_count": points, "vectors_count": vectors})
        total_points += points
    return {"collections": len(cols), "total_points": total_points, "items": items}

