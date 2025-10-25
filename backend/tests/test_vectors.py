"""
Tests for vector validation and vector routes
"""
import math

import pytest
from fastapi.testclient import TestClient


def test_vector_validation_empty_vector():
    """Test that empty vectors are rejected"""
    from app.schemas.vectors import Point

    with pytest.raises(ValueError, match="Vector cannot be empty"):
        Point(id="1", vector=[])


def test_vector_validation_nan_value():
    """Test that NaN values in vectors are rejected"""
    from app.schemas.vectors import Point

    with pytest.raises(ValueError, match="Vector contains NaN"):
        Point(id="1", vector=[1.0, 2.0, float('nan'), 4.0])


def test_vector_validation_inf_value():
    """Test that Inf values in vectors are rejected"""
    from app.schemas.vectors import Point

    with pytest.raises(ValueError, match="Vector contains Inf"):
        Point(id="1", vector=[1.0, 2.0, float('inf'), 4.0])


def test_vector_validation_too_large_dimension():
    """Test that vectors over 4096 dimensions are rejected"""
    from app.schemas.vectors import Point

    with pytest.raises(ValueError, match="Vector dimension too large"):
        Point(id="1", vector=[1.0] * 5000)


def test_vector_validation_non_numeric():
    """Test that non-numeric values in vectors are rejected"""
    from app.schemas.vectors import Point

    with pytest.raises(ValueError, match="must be a number"):
        Point(id="1", vector=[1.0, 2.0, "invalid", 4.0])


def test_vector_validation_valid_vector():
    """Test that valid vectors are accepted"""
    from app.schemas.vectors import Point

    point = Point(id="1", vector=[1.0, 2.0, 3.0, 4.0])
    assert len(point.vector) == 4
    assert point.id == "1"


def test_payload_validation_non_dict():
    """Test that non-dict payloads are rejected"""
    from app.schemas.vectors import Point

    with pytest.raises(ValueError, match="Payload must be a dictionary"):
        Point(id="1", vector=[1.0, 2.0], payload="invalid")


def test_payload_validation_valid_dict():
    """Test that dict payloads are accepted"""
    from app.schemas.vectors import Point

    point = Point(id="1", vector=[1.0, 2.0], payload={"key": "value"})
    assert point.payload == {"key": "value"}


def test_insert_vectors_dimension_mismatch():
    """Test that dimension mismatch is detected"""
    from app.schemas.vectors import InsertVectorsRequest, Point

    with pytest.raises(ValueError, match="Dimension mismatch"):
        InsertVectorsRequest(
            collection="test",
            points=[
                Point(id="1", vector=[1.0, 2.0, 3.0]),      # dim=3
                Point(id="2", vector=[4.0, 5.0, 6.0, 7.0])  # dim=4 (mismatch!)
            ]
        )


def test_insert_vectors_consistent_dimensions():
    """Test that consistent dimensions are accepted"""
    from app.schemas.vectors import InsertVectorsRequest, Point

    request = InsertVectorsRequest(
        collection="test",
        points=[
            Point(id="1", vector=[1.0, 2.0, 3.0]),
            Point(id="2", vector=[4.0, 5.0, 6.0]),
            Point(id="3", vector=[7.0, 8.0, 9.0])
        ]
    )
    assert len(request.points) == 3
    assert all(len(p.vector) == 3 for p in request.points)


def test_search_vector_validation():
    """Test search vector validation"""
    from app.schemas.vectors import SearchRequest

    # Valid search
    search = SearchRequest(
        collection="test",
        vector=[1.0, 2.0, 3.0],
        limit=10
    )
    assert len(search.vector) == 3

    # Invalid: NaN
    with pytest.raises(ValueError, match="NaN"):
        SearchRequest(
            collection="test",
            vector=[1.0, float('nan')],
            limit=10
        )


def test_insert_vectors_route_validation(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test that insert endpoint validates vectors"""
    # Test with NaN (should be rejected by validation)
    response = client.post(
        "/api/vectors/insert",
        headers=auth_headers,
        json={
            "collection": "test",
            "points": [
                {"id": "1", "vector": [1.0, 2.0, float('nan')]}
            ]
        }
    )
    # FastAPI will return 422 for validation errors
    assert response.status_code == 422


def test_insert_vectors_route_dimension_mismatch(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test that insert endpoint rejects dimension mismatch"""
    response = client.post(
        "/api/vectors/insert",
        headers=auth_headers,
        json={
            "collection": "test",
            "points": [
                {"id": "1", "vector": [1.0, 2.0]},
                {"id": "2", "vector": [3.0, 4.0, 5.0]}  # Different dimension
            ]
        }
    )
    assert response.status_code == 422
    assert "Dimension mismatch" in response.text


def test_insert_vectors_route_success(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test successful vector insertion"""
    mock_qdrant_client.upsert.return_value = None

    response = client.post(
        "/api/vectors/insert",
        headers=auth_headers,
        json={
            "collection": "test",
            "points": [
                {"id": "1", "vector": [1.0, 2.0, 3.0], "payload": {"key": "value"}},
                {"id": "2", "vector": [4.0, 5.0, 6.0]}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted"] == 2


def test_search_vectors_route(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test vector search endpoint"""
    # Mock search results
    from unittest.mock import MagicMock
    mock_result = MagicMock()
    mock_result.id = "1"
    mock_result.score = 0.95
    mock_result.payload = {"key": "value"}
    mock_qdrant_client.search.return_value = [mock_result]

    response = client.post(
        "/api/vectors/search",
        headers=auth_headers,
        json={
            "collection": "test",
            "vector": [1.0, 2.0, 3.0],
            "limit": 10
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    assert data["results"][0]["id"] == "1"
    assert data["results"][0]["score"] == 0.95


def test_delete_vectors_route(client: TestClient, auth_headers: dict, mock_settings, mock_qdrant_client):
    """Test vector deletion endpoint"""
    mock_qdrant_client.delete.return_value = None

    response = client.post(
        "/api/vectors/delete",
        headers=auth_headers,
        json={
            "collection": "test",
            "ids": ["1", "2", "3"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] == 3
