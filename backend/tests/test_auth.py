"""
Tests for authentication endpoints
"""
import pytest
from fastapi.testclient import TestClient


def test_login_success(client: TestClient, admin_password: str, mock_settings):
    """Test successful login"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": admin_password}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "csrf_token" in data
    assert len(data["csrf_token"]) > 20  # CSRF token should be sufficiently long


def test_login_wrong_username(client: TestClient, admin_password: str, mock_settings):
    """Test login with wrong username"""
    response = client.post(
        "/api/auth/login",
        json={"username": "hacker", "password": admin_password}
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_wrong_password(client: TestClient, mock_settings):
    """Test login with wrong password"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_missing_username(client: TestClient, admin_password: str):
    """Test login with missing username"""
    response = client.post(
        "/api/auth/login",
        json={"password": admin_password}
    )
    assert response.status_code == 422  # Validation error


def test_login_missing_password(client: TestClient):
    """Test login with missing password"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin"}
    )
    assert response.status_code == 422  # Validation error


def test_login_short_username(client: TestClient, admin_password: str):
    """Test login with too short username"""
    response = client.post(
        "/api/auth/login",
        json={"username": "ab", "password": admin_password}  # min_length=3
    )
    assert response.status_code == 422


def test_login_short_password(client: TestClient):
    """Test login with too short password"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "ab"}  # min_length=3
    )
    assert response.status_code == 422


def test_csrf_token_set_in_cookie(client: TestClient, admin_password: str, mock_settings):
    """Test that CSRF token is set as httponly cookie"""
    response = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": admin_password}
    )
    assert response.status_code == 200

    # Check cookie is set
    cookies = response.cookies
    assert "csrf_token" in cookies

    # Cookie should have secure attributes (checked via Set-Cookie header)
    set_cookie = response.headers.get("set-cookie", "")
    assert "csrf_token=" in set_cookie.lower()
    assert "httponly" in set_cookie.lower()
    assert "secure" in set_cookie.lower()
    assert "samesite=strict" in set_cookie.lower()
