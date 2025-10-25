from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from qdrant_client import AsyncQdrantClient

from ..core.config import Settings
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = Settings()
_qdrant: AsyncQdrantClient | None = None


async def get_qdrant_client() -> AsyncQdrantClient:
    """
    Get or create singleton async Qdrant client with connection pooling

    Returns:
        AsyncQdrantClient instance
    """
    global _qdrant
    if _qdrant is None:
        logger.info(
            "Connecting to Qdrant (async)",
            extra={
                "host": settings.qdrant_host,
                "port": settings.qdrant_port,
                "https": settings.use_https
            }
        )
        _qdrant = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.get_qdrant_api_key(),
            https=settings.use_https,
            timeout=settings.qdrant_timeout,
            # Connection pooling configuration
            grpc_port=6334,  # gRPC for better performance
            prefer_grpc=True,
        )
        # Sanity check connection
        try:
            await _qdrant.get_collections()
            logger.info("Qdrant async connection established")
        except Exception as e:
            logger.error(
                "Failed to connect to Qdrant",
                exc_info=True,
                extra={"error": str(e)}
            )
            _qdrant = None
            raise
    return _qdrant


@asynccontextmanager
async def qdrant_client() -> AsyncGenerator[AsyncQdrantClient, None]:
    """
    Async context manager for Qdrant client (dependency injection pattern)

    Usage:
        async with qdrant_client() as client:
            await client.get_collections()
    """
    client = await get_qdrant_client()
    try:
        yield client
    except Exception as e:
        logger.error(
            "Qdrant operation failed",
            exc_info=True,
            extra={"error": str(e)}
        )
        raise


def reset_qdrant_client() -> None:
    """
    Reset Qdrant client (forces reconnection on next call)
    Used after key rotation.
    """
    global _qdrant
    if _qdrant is not None:
        logger.info("Resetting Qdrant client")
    _qdrant = None


async def close_qdrant_client() -> None:
    """
    Close Qdrant client connection gracefully
    Called during application shutdown.
    """
    global _qdrant
    if _qdrant is not None:
        try:
            await _qdrant.close()
            logger.info("Qdrant async client closed")
        except Exception as e:
            logger.warning(
                "Error closing Qdrant client",
                extra={"error": str(e)}
            )
        finally:
            _qdrant = None

