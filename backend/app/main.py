"""
QuietVector API
Sade, güvenli Qdrant yönetim arayüzünün FastAPI backend'i.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from .routes import auth as auth_routes
from .routes import collections as collections_routes
from .routes import vectors as vectors_routes
from .routes import snapshots as snapshots_routes
from .routes import stats as stats_routes
from .routes import security as security_routes

from .core.config import Settings
from .core.logging import setup_logging, get_logger
from .core.middleware import (
    AuditLogMiddleware,
    BodySizeLimitMiddleware,
    CSRFMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
)
from .qdrant.client import close_qdrant_client

settings = Settings()

# Setup structured logging
setup_logging(settings)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan events
    Handles startup and shutdown tasks
    """
    # Startup
    logger.info(
        "QuietVector starting",
        extra={
            "version": app.version,
            "api_host": settings.api_host,
            "api_port": settings.api_port
        }
    )
    yield
    # Shutdown
    logger.info("QuietVector shutting down")
    await close_qdrant_client()
    logger.info("Qdrant client closed gracefully")


app = FastAPI(
    title="QuietVector API",
    version="0.1.0",
    lifespan=lifespan
)

# Metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# CORS (sadece belirli origin)
if settings.frontend_origin:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Protections & audit
# Order matters: RequestID → BodySize → RateLimit → CSRF → Audit
app.add_middleware(RequestIDMiddleware)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_size_bytes)
app.add_middleware(RateLimitMiddleware, per_minute=settings.rate_limit_per_minute)
app.add_middleware(CSRFMiddleware)
app.add_middleware(AuditLogMiddleware, path=settings.audit_log_path)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception",
        exc_info=True,
        extra={
            "method": request.method,
            "path": str(request.url.path),
            "client": request.client.host if request.client else None,
            "error_type": type(exc).__name__
        }
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )


@app.get("/health")
def health():
    return {"status": "ok"}



# Routers (prefix all under /api)
api = APIRouter()
api.include_router(auth_routes.router)
api.include_router(collections_routes.router)
api.include_router(vectors_routes.router)
api.include_router(snapshots_routes.router)
api.include_router(stats_routes.router)
api.include_router(security_routes.router)
app.include_router(api, prefix="/api")
