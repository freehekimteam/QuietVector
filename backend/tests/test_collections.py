"""
Tests for collections routes
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


def test_list_collections_empty(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test listing collections when none exist"""
    mock_qdrant_client.get_collections.return_value.collections = []

    response = client.get("/api/collections", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["collections"] == []


def test_list_collections_with_data(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test listing collections with existing collections"""
    # Mock collection
    mock_collection = MagicMock()
    mock_collection.name = "test_collection"
    mock_qdrant_client.get_collections.return_value.collections = [mock_collection]

    response = client.get("/api/collections", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["collections"]) == 1
    assert data["collections"][0]["name"] == "test_collection"


def test_get_collection_info(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test getting collection info"""
    # Mock collection config
    mock_config = MagicMock()
    mock_config.params.vectors.size = 128
    mock_config.params.vectors.distance = "Cosine"
    mock_qdrant_client.get_collection.return_value.config = mock_config

    mock_qdrant_client.count.return_value.count = 1000

    response = client.get("/api/collections/test_col", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_col"
    assert data["vectors_count"] == 1000
    assert data["vector_size"] == 128
    assert data["distance"] == "Cosine"


def test_create_collection_cosine(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test creating collection with Cosine distance"""
    mock_qdrant_client.create_collection.return_value = True

    response = client.post(
        "/api/collections",
        headers=auth_headers,
        json={
            "name": "test_col",
            "vectors_size": 128,
            "distance": "Cosine"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_col"
    assert data["created"] is True


def test_create_collection_dot(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test creating collection with Dot distance"""
    mock_qdrant_client.create_collection.return_value = True

    response = client.post(
        "/api/collections",
        headers=auth_headers,
        json={
            "name": "test_col",
            "vectors_size": 256,
            "distance": "Dot"
        }
    )
    assert response.status_code == 200


def test_create_collection_euclid(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test creating collection with Euclid distance"""
    mock_qdrant_client.create_collection.return_value = True

    response = client.post(
        "/api/collections",
        headers=auth_headers,
        json={
            "name": "test_col",
            "vectors_size": 512,
            "distance": "Euclid"
        }
    )
    assert response.status_code == 200


def test_create_collection_invalid_distance(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test creating collection with invalid distance"""
    response = client.post(
        "/api/collections",
        headers=auth_headers,
        json={
            "name": "test_col",
            "vectors_size": 128,
            "distance": "InvalidDistance"
        }
    )
    assert response.status_code == 422  # Validation error


def test_create_collection_empty_name(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test creating collection with empty name"""
    response = client.post(
        "/api/collections",
        headers=auth_headers,
        json={
            "name": "",
            "vectors_size": 128,
            "distance": "Cosine"
        }
    )
    assert response.status_code == 422


def test_create_collection_zero_size(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test creating collection with zero vector size"""
    response = client.post(
        "/api/collections",
        headers=auth_headers,
        json={
            "name": "test_col",
            "vectors_size": 0,
            "distance": "Cosine"
        }
    )
    assert response.status_code == 422


def test_create_collection_negative_size(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test creating collection with negative vector size"""
    response = client.post(
        "/api/collections",
        headers=auth_headers,
        json={
            "name": "test_col",
            "vectors_size": -100,
            "distance": "Cosine"
        }
    )
    assert response.status_code == 422


def test_delete_collection(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test deleting collection"""
    mock_qdrant_client.delete_collection.return_value = True

    response = client.delete("/api/collections/test_col", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True


def test_collections_require_auth(client: TestClient, mock_settings, mock_qdrant_client):
    """Test that collections endpoints require authentication"""
    # No auth header
    response = client.get("/api/collections")
    assert response.status_code == 401  # Unauthorized

    response = client.post(
        "/api/collections",
        json={"name": "test", "vectors_size": 128, "distance": "Cosine"}
    )
    assert response.status_code == 401


def test_collections_require_csrf(client: TestClient, auth_token: str, mock_settings, mock_qdrant_client):
    """Test that POST/DELETE require CSRF token"""
    # Auth but no CSRF
    response = client.post(
        "/api/collections",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"name": "test", "vectors_size": 128, "distance": "Cosine"}
    )
    assert response.status_code == 403  # CSRF forbidden
