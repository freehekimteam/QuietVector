"""
Vector Service
Handles business logic for vector operations
"""
from __future__ import annotations

from typing import Any

from qdrant_client import AsyncQdrantClient, models as qm

from ..core.logging import get_logger
from ..schemas.vectors import DeleteRequest, InsertVectorsRequest, SearchRequest

logger = get_logger(__name__)


class VectorService:
    """Service for managing vectors in Qdrant"""

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def insert_vectors(self, request: InsertVectorsRequest) -> dict[str, int]:
        """
        Insert or update vectors in a collection

        Args:
            request: Insert vectors request with collection and points

        Returns:
            Dictionary with number of inserted vectors

        Raises:
            Exception: If insertion fails
        """
        # Convert schema to Qdrant points
        points = [
            qm.PointStruct(
                id=p.id,
                vector=p.vector,
                payload=p.payload or {}
            )
            for p in request.points
        ]

        # Perform upsert
        await self.client.upsert(
            collection_name=request.collection,
            points=points,
            wait=True
        )

        logger.info(
            "Vectors inserted",
            extra={
                "collection": request.collection,
                "count": len(points),
                "dimension": len(request.points[0].vector) if request.points else 0
            }
        )

        return {"inserted": len(points)}

    async def search_vectors(self, request: SearchRequest) -> dict[str, list[dict[str, Any]]]:
        """
        Search for similar vectors

        Args:
            request: Search request with query vector and parameters

        Returns:
            Dictionary with search results
        """
        results = await self.client.search(
            collection_name=request.collection,
            query_vector=request.vector,
            limit=request.limit,
            with_payload=request.with_payload
        )

        # Format results
        formatted_results = [
            {
                "id": str(r.id),
                "score": float(r.score),
                "payload": r.payload if request.with_payload else None
            }
            for r in results
        ]

        logger.info(
            "Vector search completed",
            extra={
                "collection": request.collection,
                "results_count": len(formatted_results),
                "limit": request.limit
            }
        )

        return {"results": formatted_results}

    async def delete_vectors(self, request: DeleteRequest) -> dict[str, int]:
        """
        Delete vectors from collection

        Args:
            request: Delete request with collection and IDs

        Returns:
            Dictionary with number of deleted vectors
        """
        await self.client.delete(
            collection_name=request.collection,
            points_selector=qm.PointIdsList(points=request.ids)
        )

        logger.info(
            "Vectors deleted",
            extra={
                "collection": request.collection,
                "count": len(request.ids)
            }
        )

        return {"deleted": len(request.ids)}
