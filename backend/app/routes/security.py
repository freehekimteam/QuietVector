from __future__ import annotations

import os
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.config import Settings
from ..core.ops import tracker
from ..core.security import verify_password_hash
from ..qdrant.client import reset_qdrant_client
from ..schemas.security import PrepareKeyRequest, PrepareKeyResponse

router = APIRouter(prefix="/security", tags=["Security"])
settings = Settings()


@router.post("/qdrant_key/prepare", response_model=PrepareKeyResponse)
def prepare_qdrant_key(body: PrepareKeyRequest) -> PrepareKeyResponse:
    # Re-auth with password
    if not settings.admin_password_hash:
        raise HTTPException(status_code=500, detail="Admin password not configured")
    if not verify_password_hash(body.admin_password, settings.admin_password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Ensure file path is configured
    key_file = settings.qdrant_api_key_file
    if not key_file:
        raise HTTPException(status_code=400, detail="QDRANT_API_KEY_FILE not configured on server")

    # Write new key securely (0600)
    try:
        key_file.parent.mkdir(parents=True, exist_ok=True)
        data = (body.new_key or "").strip()
        if len(data) < 16:
            raise ValueError("Key too short")
        with open(key_file, 'w', encoding='utf-8') as f:
            f.write(data)
        os.chmod(key_file, 0o600)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write key file: {e}")

    # Reset qdrant client so next call uses new key after restart
    reset_qdrant_client()

    # Prepare ops info and suggested commands (no direct docker control by default)
    op = tracker.create("qdrant_key_prepare", meta={"file": str(key_file)})
    apply_instructions: List[str] = [
        "# 1) Ensure compose env mounts key file to Qdrant or uses env reference",
        "# 2) Restart Qdrant service to apply new key:",
        "docker compose -f deployment/docker/docker-compose.server.yml up -d qdrant",
        "# 3) Verify: curl -H 'api-key: <NEW_KEY>' http://localhost:6333/healthz",
    ]
    return PrepareKeyResponse(op_id=op.id, apply_instructions=apply_instructions)

