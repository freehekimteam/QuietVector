from __future__ import annotations

import json
import logging
import secrets
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .config import Settings
from .logging import get_logger

logger = get_logger(__name__)
settings = Settings()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        rid = str(uuid.uuid4())
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            dur_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "Request completed",
                extra={
                    "request_id": rid,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": int(dur_ms),
                    "status_code": response.status_code if hasattr(response, 'status_code') else None
                }
            )
        response.headers["X-Request-ID"] = rid
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        super().__init__(app)
        self.max = max_bytes

    async def dispatch(self, request: Request, call_next: Callable):
        try:
            cl = request.headers.get("content-length")
            if cl is not None and int(cl) > self.max:
                return JSONResponse(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, content={"error": "Request body too large"})
        except Exception:
            pass
        return await call_next(request)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection for state-changing operations.
    Validates X-CSRF-Token header against csrf_token cookie.
    """
    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    EXEMPT_PATHS = {"/api/auth/login", "/health", "/metrics"}

    async def dispatch(self, request: Request, call_next: Callable):
        # Skip CSRF check for safe methods
        if request.method in self.SAFE_METHODS:
            return await call_next(request)

        # Skip CSRF check for exempt paths (like login)
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Validate CSRF token
        header_token = request.headers.get("X-CSRF-Token", "")
        cookie_token = request.cookies.get("csrf_token", "")

        if not header_token or not cookie_token:
            logger.warning(
                "CSRF validation failed: missing token",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "has_header": bool(header_token),
                    "has_cookie": bool(cookie_token)
                }
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "CSRF token missing"}
            )

        if not secrets.compare_digest(header_token, cookie_token):
            logger.warning(
                "CSRF validation failed: token mismatch",
                extra={
                    "path": request.url.path,
                    "method": request.method
                }
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "CSRF token invalid"}
            )

        return await call_next(request)


class RateLimitCleanupMixin:
    """Mixin for cleaning up old rate limit entries"""

    def cleanup_stale(self, max_age_seconds: float = 300.0) -> int:
        """Remove IP entries with no recent activity"""
        if not hasattr(self, 'state'):
            return 0

        now = time.monotonic()
        removed = 0
        stale_ips = []

        for ip, q in self.state.items():
            # Remove old timestamps
            while q and now - q[0] > max_age_seconds:
                q.popleft()
            # If queue is empty, mark IP for removal
            if not q:
                stale_ips.append(ip)

        for ip in stale_ips:
            del self.state[ip]
            removed += 1

        if removed > 0:
            logger.info(
                "RateLimiter cleanup completed",
                extra={"removed_ips": removed}
            )

        return removed


class RateLimitMiddleware(BaseHTTPMiddleware, RateLimitCleanupMixin):
    def __init__(self, app: ASGIApp, per_minute: int) -> None:
        super().__init__(app)
        self.limit = per_minute
        self.window = 60.0
        self.state: dict[str, deque[float]] = defaultdict(deque)
        self.last_cleanup = time.monotonic()

    def _ip(self, request: Request) -> str:
        xfwd = request.headers.get("x-forwarded-for")
        if xfwd:
            return xfwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable):
        now = time.monotonic()
        ip = self._ip(request)
        q = self.state[ip]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content={"error": "Rate limit exceeded"})
        q.append(now)

        # Periodic cleanup (every 5 minutes)
        if now - self.last_cleanup > 300:
            self.cleanup_stale()
            self.last_cleanup = now

        return await call_next(request)


class AuditLogMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, path: Path) -> None:
        super().__init__(app)
        self.path = path
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    async def dispatch(self, request: Request, call_next: Callable):
        start = time.time()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            try:
                entry = {
                    "ts": int(start),
                    "method": request.method,
                    "path": request.url.path,
                    "status": getattr(response, "status_code", 0),
                    "client": request.client.host if request.client else None,
                }
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception:
                pass

