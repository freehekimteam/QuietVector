from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..core.config import Settings
from ..core.security import create_access_token, verify_password_hash
from ..schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = Settings()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    if body.username != settings.admin_username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not settings.admin_password_hash:
        raise HTTPException(status_code=500, detail="Admin password not configured")
    if not verify_password_hash(body.password, settings.admin_password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(sub=body.username)
    return TokenResponse(access_token=token)

