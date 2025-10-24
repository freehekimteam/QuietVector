from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Environment
    env: Literal["staging", "production", "development"] = Field(
        default="staging", description="Application environment"
    )

    # API
    api_host: str = Field(default="127.0.0.1", description="API bind host")
    api_port: int = Field(default=8090, ge=1024, le=65535)
    frontend_origin: str | None = Field(default=None, description="Allowed CORS origin")

    # Qdrant
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333, ge=1, le=65535)
    qdrant_api_key: SecretStr | None = Field(default=None)
    qdrant_timeout: float = Field(default=10.0, ge=0.1)

    # Auth (JWT)
    jwt_secret: SecretStr = Field(default=SecretStr("change_this_secret"))
    token_expire_minutes: int = Field(default=60, ge=5, le=24 * 60)
    admin_username: str = Field(default="admin", min_length=3)
    admin_password_hash: str = Field(default="", description="argon2 hash")

    # API Key (optional)
    require_api_key: bool = Field(default=False)
    api_key: SecretStr | None = Field(default=None)

    # Protections
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)
    max_body_size_bytes: int = Field(default=1048576, ge=1024, le=10_485_760)

    # Audit Log
    audit_log_path: Path = Field(default=Path("/var/log/quietvector/audit.log"))
    log_json: bool = Field(default=True)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    def get_qdrant_api_key(self) -> str | None:
        return self.qdrant_api_key.get_secret_value() if self.qdrant_api_key else None

    def get_jwt_secret(self) -> str:
        return self.jwt_secret.get_secret_value()

    def get_api_key(self) -> str | None:
        return self.api_key.get_secret_value() if self.api_key else None

    @property
    def use_https(self) -> bool:
        return self.qdrant_port == 443

