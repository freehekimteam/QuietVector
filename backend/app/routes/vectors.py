from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from qdrant_client import models as qm

from ..qdrant.client import get_qdrant_client
from ..schemas.vectors import DeleteRequest, InsertVectorsRequest, SearchRequest
from .deps import require_auth

router = APIRouter(prefix="/vectors", tags=["Vectors"])


@router.post("/insert")
def insert_vectors(body: InsertVectorsRequest, _: str = Depends(require_auth)) -> dict:
    c = get_qdrant_client()
    points = [
        qm.PointStruct(id=p.id, vector=p.vector, payload=p.payload or {}) for p in body.points
    ]
    try:
        c.upsert(collection_name=body.collection, points=points, wait=True)
        return {"inserted": len(points)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search")
def search(body: SearchRequest, _: str = Depends(require_auth)) -> dict:
    c = get_qdrant_client()
    try:
        res = c.search(
            collection_name=body.collection,
            query_vector=body.vector,
            limit=body.limit,
            with_payload=body.with_payload,
        )
        out = [
            {
                "id": str(r.id),
                "score": float(r.score),
                "payload": r.payload,
            }
            for r in res
        ]
        return {"results": out}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/delete")
def delete_points(body: DeleteRequest, _: str = Depends(require_auth)) -> dict:
    c = get_qdrant_client()
    try:
        c.delete(collection_name=body.collection, points_selector=qm.PointIdsList(points=body.ids))
        return {"deleted": len(body.ids)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

