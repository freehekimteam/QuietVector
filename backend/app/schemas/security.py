from __future__ import annotations

from pydantic import BaseModel, Field


class PrepareKeyRequest(BaseModel):
    new_key: str = Field(..., min_length=16, max_length=256)
    admin_password: str = Field(..., min_length=3)


class PrepareKeyResponse(BaseModel):
    op_id: str
    apply_instructions: list[str]


class OpsApplyRequest(BaseModel):
    admin_password: str
    dry_run: bool = False


class OpsApplyResponse(BaseModel):
    executed: bool
    mode: str
    command: list[str]
    rc: int | None = None
    stdout: str | None = None
    stderr: str | None = None
