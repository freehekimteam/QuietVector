"""
Collection Service
Handles business logic for Qdrant collection operations
"""
from __future__ import annotations

from typing import Any

from qdrant_client import AsyncQdrantClient, models as qm

from ..core.logging import get_logger
from ..schemas.collections import CollectionInfo, CreateCollectionRequest

logger = get_logger(__name__)


class CollectionService:
    """Service for managing Qdrant collections"""

    def __init__(self, client: AsyncQdrantClient):
        self.client = client

    async def list_collections(self) -> list[dict[str, Any]]:
        """
        List all collections with basic info

        Returns:
            List of collection information dictionaries
        """
        collections = await self.client.get_collections()
        return [{"name": c.name} for c in collections.collections]

    async def get_collection_info(self, collection_name: str) -> CollectionInfo:
        """
        Get detailed information about a collection

        Args:
            collection_name: Name of the collection

        Returns:
            CollectionInfo with details

        Raises:
            Exception: If collection doesn't exist
        """
        # Get collection config
        collection = await self.client.get_collection(collection_name)

        # Get vector count
        count_result = await self.client.count(collection_name)

        # Extract vector size and distance
        vector_config = collection.config.params.vectors
        vector_size = vector_config.size if hasattr(vector_config, 'size') else 0
        distance = str(vector_config.distance) if hasattr(vector_config, 'distance') else "Unknown"

        logger.info(
            "Retrieved collection info",
            extra={
                "collection": collection_name,
                "vectors_count": count_result.count,
                "vector_size": vector_size
            }
        )

        return CollectionInfo(
            name=collection_name,
            vectors_count=count_result.count,
            vector_size=vector_size,
            distance=distance
        )

    async def create_collection(self, request: CreateCollectionRequest) -> dict[str, Any]:
        """
        Create a new collection

        Args:
            request: Collection creation parameters

        Returns:
            Dictionary with creation status
        """
        # Map distance string to Qdrant enum
        distance_map = {
            "Cosine": qm.Distance.COSINE,
            "Dot": qm.Distance.DOT,
            "Euclid": qm.Distance.EUCLID,
        }
        distance = distance_map.get(request.distance, qm.Distance.COSINE)

        # Create collection
        result = await self.client.create_collection(
            collection_name=request.name,
            vectors_config=qm.VectorParams(
                size=request.vectors_size,
                distance=distance
            )
        )

        logger.info(
            "Collection created",
            extra={
                "collection": request.name,
                "vector_size": request.vectors_size,
                "distance": request.distance
            }
        )

        return {
            "name": request.name,
            "created": result
        }

    async def delete_collection(self, collection_name: str) -> dict[str, bool]:
        """
        Delete a collection

        Args:
            collection_name: Name of collection to delete

        Returns:
            Dictionary with deletion status
        """
        result = await self.client.delete_collection(collection_name)

        logger.info(
            "Collection deleted",
            extra={"collection": collection_name}
        )

        return {"deleted": result}
