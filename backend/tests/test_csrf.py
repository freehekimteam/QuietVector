"""
Tests for CSRF middleware protection
"""
import pytest
from fastapi.testclient import TestClient


def test_csrf_get_request_allowed(client: TestClient, auth_token: str, mock_settings):
    """Test that GET requests bypass CSRF check"""
    response = client.get(
        "/health",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    # GET requests should not require CSRF token
    assert response.status_code == 200


def test_csrf_post_without_token_rejected(client: TestClient, auth_token: str, mock_settings, mock_qdrant_client):
    """Test that POST without CSRF token is rejected"""
    response = client.post(
        "/api/collections",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "test_col", "vectors_size": 128, "distance": "Cosine"}
    )
    assert response.status_code == 403
    assert "CSRF" in response.json()["error"]


def test_csrf_post_with_valid_token_allowed(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test that POST with valid CSRF token is allowed"""
    response = client.post(
        "/api/collections",
        headers=auth_headers,
        json={"name": "test_col", "vectors_size": 128, "distance": "Cosine"}
    )
    # Should pass CSRF check (might fail for other reasons like Qdrant connection)
    assert response.status_code != 403  # Not CSRF error


def test_csrf_login_exempt(client: TestClient, admin_password: str, mock_settings):
    """Test that login endpoint is exempt from CSRF"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": admin_password}
    )
    # Login should work without CSRF token (it's how we get the token!)
    assert response.status_code == 200


def test_csrf_health_exempt(client: TestClient):
    """Test that health endpoint is exempt from CSRF"""
    response = client.post("/health")
    # Health should be accessible (even though it's GET only, testing POST)
    # This will fail with 405 Method Not Allowed, not 403 CSRF
    assert response.status_code == 405  # Method not allowed, not CSRF forbidden


def test_csrf_mismatch_token_rejected(client: TestClient, auth_token: str, mock_settings, mock_qdrant_client):
    """Test that mismatched CSRF token is rejected"""
    client.cookies.set("csrf_token", "valid_cookie_token")

    response = client.post(
        "/api/collections",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "X-CSRF-Token": "wrong_header_token"
        },
        json={"name": "test_col", "vectors_size": 128, "distance": "Cosine"}
    )
    assert response.status_code == 403
    assert "CSRF" in response.json()["error"]


def test_csrf_missing_cookie_rejected(client: TestClient, auth_token: str, mock_settings, mock_qdrant_client):
    """Test that missing CSRF cookie is rejected"""
    response = client.post(
        "/api/collections",
        headers={
            "Authorization": f"Bearer {auth_token}",
            "X-CSRF-Token": "some_token"
        },
        json={"name": "test_col", "vectors_size": 128, "distance": "Cosine"}
    )
    assert response.status_code == 403


def test_csrf_missing_header_rejected(client: TestClient, auth_token: str, mock_settings, mock_qdrant_client):
    """Test that missing CSRF header is rejected"""
    client.cookies.set("csrf_token", "some_token")

    response = client.post(
        "/api/collections",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "test_col", "vectors_size": 128, "distance": "Cosine"}
    )
    assert response.status_code == 403


def test_csrf_options_request_allowed(client: TestClient):
    """Test that OPTIONS requests bypass CSRF"""
    response = client.options("/api/collections")
    # OPTIONS should not require CSRF
    # Status might be 200 or 405 depending on CORS config
    assert response.status_code != 403


def test_csrf_head_request_allowed(client: TestClient):
    """Test that HEAD requests bypass CSRF"""
    response = client.head("/health")
    # HEAD should not require CSRF
    assert response.status_code != 403
