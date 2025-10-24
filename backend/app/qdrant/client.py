from __future__ import annotations

import logging
from typing import Any

from qdrant_client import QdrantClient

from ..core.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()
_qdrant: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _qdrant
    if _qdrant is None:
        logger.info(
            "Connecting to Qdrant %s:%s (https=%s)",
            settings.qdrant_host,
            settings.qdrant_port,
            settings.use_https,
        )
        _qdrant = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.get_qdrant_api_key(),
            https=settings.use_https,
            timeout=settings.qdrant_timeout,
        )
        # sanity
        _qdrant.get_collections()
        logger.info("Qdrant connection OK")
    return _qdrant


def reset_qdrant_client() -> None:
    global _qdrant
    _qdrant = None

