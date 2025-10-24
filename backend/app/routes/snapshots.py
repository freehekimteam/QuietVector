from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..core.config import Settings
from .deps import require_auth

router = APIRouter(prefix="/snapshots", tags=["Snapshots"])
settings = Settings()


def _base_url() -> str:
    scheme = "https" if settings.use_https else "http"
    return f"{scheme}://{settings.qdrant_host}:{settings.qdrant_port}"


def _headers() -> dict[str, str]:
    h: dict[str, str] = {}
    if settings.get_qdrant_api_key():
        h["api-key"] = settings.get_qdrant_api_key() or ""
    return h


@router.get("/{collection}")
def list_snapshots(collection: str, _: str = Depends(require_auth)) -> dict:
    url = f"{_base_url()}/collections/{collection}/snapshots"
    try:
        with httpx.Client(timeout=settings.qdrant_timeout) as client:
            r = client.get(url, headers=_headers())
            if r.status_code != 200:
                raise HTTPException(status_code=r.status_code, detail=r.text)
            return r.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{collection}")
def create_snapshot(collection: str, _: str = Depends(require_auth)) -> dict:
    url = f"{_base_url()}/collections/{collection}/snapshots"
    try:
        with httpx.Client(timeout=settings.qdrant_timeout) as client:
            r = client.post(url, headers=_headers())
            if r.status_code not in (200, 202):
                raise HTTPException(status_code=r.status_code, detail=r.text)
            return r.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{collection}/{name}")
def download_snapshot(collection: str, name: str, _: str = Depends(require_auth)):
    # Stream download through API
    url = f"{_base_url()}/collections/{collection}/snapshots/{name}"
    try:
        client = httpx.Client(timeout=None)
        r = client.get(url, headers=_headers(), stream=True)
        if r.status_code != 200:
            client.close()
            raise HTTPException(status_code=r.status_code, detail=r.text)

        def _iter():
            with client:
                for chunk in r.iter_bytes():
                    yield chunk

        return StreamingResponse(
            _iter(),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={name}"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

