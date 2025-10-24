from __future__ import annotations

import json
import logging
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

logger = logging.getLogger(__name__)
settings = Settings()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        rid = str(uuid.uuid4())
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            dur_ms = (time.perf_counter() - start) * 1000
            logger.info(f"{request.method} {request.url.path} {int(dur_ms)}ms rid={rid}")
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


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, per_minute: int) -> None:
        super().__init__(app)
        self.limit = per_minute
        self.window = 60.0
        self.state: dict[str, deque[float]] = defaultdict(deque)

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

