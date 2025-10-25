from __future__ import annotations

import secrets
from fastapi import APIRouter, HTTPException, Response, status

from ..core.config import Settings
from ..core.security import create_access_token, verify_password_hash
from ..schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = Settings()


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, response: Response) -> TokenResponse:
    if body.username != settings.admin_username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not settings.admin_password_hash:
        raise HTTPException(status_code=500, detail="Admin password not configured")
    if not verify_password_hash(body.password, settings.admin_password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Create JWT token
    token = create_access_token(sub=body.username)

    # Generate and set CSRF token cookie
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="strict",
        max_age=settings.token_expire_minutes * 60,
    )

    return TokenResponse(access_token=token, csrf_token=csrf_token)

