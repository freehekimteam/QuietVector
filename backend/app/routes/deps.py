from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

from ..core.config import Settings
from ..core.security import decode_access_token

settings = Settings()


def require_auth(request: Request) -> str:
    # Optional API key
    if settings.require_api_key:
        provided = request.headers.get("x-api-key") or request.headers.get("X-Api-Key")
        if not provided or provided != (settings.get_api_key() or ""):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
        return str(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

