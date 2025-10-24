from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse

from ..core.config import Settings
from ..core.ops import tracker
import os
import tempfile
from pathlib import Path
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


@router.post("/{collection}/restore")
async def restore_snapshot(collection: str, file: UploadFile = File(...), _: str = Depends(require_auth)) -> dict:
    """Restore a collection from a snapshot file (streamed upload)."""
    url = f"{_base_url()}/collections/{collection}/snapshots/upload"
    try:
        # Stream file to Qdrant using multipart form-data
        async with httpx.AsyncClient(timeout=None) as client:
            files = {"snapshot": (file.filename or "snapshot.tar", file.file, "application/octet-stream")}
            r = await client.post(url, headers=_headers(), files=files)
        if r.status_code not in (200, 202):
            raise HTTPException(status_code=r.status_code, detail=r.text)
        return r.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _do_upload(op_id: str, collection: str, tmp_path: Path) -> None:
    tracker.update(op_id, stage="uploading")
    url = f"{_base_url()}/collections/{collection}/snapshots/upload"
    try:
        with httpx.Client(timeout=None) as client:
            with tmp_path.open("rb") as f:
                files = {"snapshot": (tmp_path.name, f, "application/octet-stream")}
                r = client.post(url, headers=_headers(), files=files)
        if r.status_code not in (200, 202):
            tracker.update(op_id, stage="failed", error=f"{r.status_code}: {r.text[:400]}")
        else:
            tracker.update(op_id, stage="completed")
    except Exception as e:
        tracker.update(op_id, stage="failed", error=str(e))
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


@router.post("/{collection}/restore_async")
async def restore_snapshot_async(
    collection: str,
    background: BackgroundTasks,
    file: UploadFile = File(...),
    _: str = Depends(require_auth),
) -> dict:
    """Async restore: save upload to temp, return op_id and perform upload in background."""
    op = tracker.create("snapshot_restore", meta={"collection": collection, "filename": file.filename or "snapshot.tar"})
    tracker.update(op.id, stage="saving")
    try:
        tmp_dir = Path(tempfile.gettempdir()) / "quietvector"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / f"{op.id}.snapshot"
        total = 0
        with tmp_path.open("wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                out.write(chunk)
        tracker.update(op.id, meta={"bytes_total": total})
    except Exception as e:
        tracker.update(op.id, stage="failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    # Kick background upload
    background.add_task(_do_upload, op.id, collection, tmp_path)
    return {"op_id": op.id, "stage": tracker.get(op.id).stage}


@router.get("/restore_status/{op_id}")
def restore_status(op_id: str, _: str = Depends(require_auth)) -> dict:
    try:
        return tracker.to_dict(op_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Operation not found")
