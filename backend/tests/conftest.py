"""
Pytest fixtures for QuietVector tests
"""
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import Settings


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def admin_password() -> str:
    """Test admin password"""
    return "test_password_123"


@pytest.fixture
def admin_password_hash(admin_password: str) -> str:
    """Argon2 hash of admin password"""
    ph = PasswordHasher()
    return ph.hash(admin_password)


@pytest.fixture
def mock_settings(admin_password_hash: str, tmp_path: Path) -> Generator[Settings, None, None]:
    """Mock settings with test values"""
    with patch('app.routes.auth.settings') as mock_auth_settings, \
         patch('app.routes.security.settings') as mock_sec_settings, \
         patch('app.core.middleware.settings') as mock_mw_settings:

        # Create test settings
        settings = Settings(
            admin_username="admin",
            admin_password_hash=admin_password_hash,
            jwt_secret="test_secret_key_for_testing_only",
            token_expire_minutes=60,
            audit_log_path=tmp_path / "audit.log",
            rate_limit_per_minute=100,
            max_body_size_bytes=1048576,
        )

        # Apply to all mocked settings
        for mock in [mock_auth_settings, mock_sec_settings, mock_mw_settings]:
            for attr in dir(settings):
                if not attr.startswith('_'):
                    setattr(mock, attr, getattr(settings, attr))

        yield settings


@pytest.fixture
def auth_token(client: TestClient, admin_password: str, mock_settings: Settings) -> str:
    """Generate valid JWT token"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": admin_password}
    )
    assert response.status_code == 200
    data = response.json()
    return data["access_token"]


@pytest.fixture
def csrf_token(client: TestClient, admin_password: str, mock_settings: Settings) -> str:
    """Get CSRF token from login"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": admin_password}
    )
    assert response.status_code == 200
    data = response.json()
    return data["csrf_token"]


@pytest.fixture
def auth_headers(auth_token: str, csrf_token: str) -> dict:
    """Headers with auth and CSRF token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "X-CSRF-Token": csrf_token
    }


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for testing without real Qdrant instance"""
    with patch('app.qdrant.client.QdrantClient') as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Mock common methods
        mock_instance.get_collections.return_value.collections = []
        mock_instance.get_collection.return_value = MagicMock(
            config=MagicMock(
                params=MagicMock(
                    vectors=MagicMock(size=128, distance="Cosine")
                )
            )
        )
        mock_instance.upsert.return_value = MagicMock()
        mock_instance.search.return_value = []

        yield mock_instance
