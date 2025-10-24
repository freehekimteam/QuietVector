"""
QuietVector API
Sade, güvenli Qdrant yönetim arayüzünün FastAPI backend'i.
"""
from __future__ import annotations

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from .routes import auth as auth_routes
from .routes import collections as collections_routes
from .routes import vectors as vectors_routes
from .routes import snapshots as snapshots_routes
from .routes import stats as stats_routes

from .core.config import Settings
from .core.middleware import (
    AuditLogMiddleware,
    BodySizeLimitMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
)

settings = Settings()

app = FastAPI(title="QuietVector API", version="0.1.0")

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
app.add_middleware(RequestIDMiddleware)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=settings.max_body_size_bytes)
app.add_middleware(RateLimitMiddleware, per_minute=settings.rate_limit_per_minute)
app.add_middleware(AuditLogMiddleware, path=settings.audit_log_path)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.getLogger(__name__).error(f"Unhandled: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )


@app.get("/health")
def health():
    return {"status": "ok"}



# Routers
app.include_router(auth_routes.router)
app.include_router(collections_routes.router)
app.include_router(vectors_routes.router)
app.include_router(snapshots_routes.router)
app.include_router(stats_routes.router)
