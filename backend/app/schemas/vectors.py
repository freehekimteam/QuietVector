from __future__ import annotations

import math
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, ValidationInfo


class Point(BaseModel):
    id: str | int
    vector: list[float]
    payload: dict[str, Any] | None = None

    @field_validator('vector')
    @classmethod
    def validate_vector(cls, v: list[float]) -> list[float]:
        if not v:
            raise ValueError("Vector cannot be empty")

        if len(v) > 4096:
            raise ValueError(f"Vector dimension too large: {len(v)} (max: 4096)")

        # Check for NaN or Inf values
        for i, val in enumerate(v):
            if not isinstance(val, (int, float)):
                raise ValueError(f"Vector element at index {i} must be a number, got {type(val).__name__}")
            if math.isnan(val):
                raise ValueError(f"Vector contains NaN at index {i}")
            if math.isinf(val):
                raise ValueError(f"Vector contains Inf at index {i}")

        return v

    @field_validator('payload')
    @classmethod
    def validate_payload(cls, v: dict[str, Any] | None) -> dict[str, Any] | None:
        if v is not None and not isinstance(v, dict):
            raise ValueError("Payload must be a dictionary")
        return v


class InsertVectorsRequest(BaseModel):
    collection: str = Field(..., min_length=1)
    points: list[Point] = Field(..., min_items=1)

    @field_validator('points')
    @classmethod
    def validate_dimension_consistency(cls, v: list[Point]) -> list[Point]:
        if not v:
            return v

        # Check all vectors have the same dimension
        first_dim = len(v[0].vector)
        for i, point in enumerate(v[1:], start=1):
            if len(point.vector) != first_dim:
                raise ValueError(
                    f"Dimension mismatch: point 0 has dimension {first_dim}, "
                    f"but point {i} has dimension {len(point.vector)}"
                )

        return v


class SearchRequest(BaseModel):
    collection: str
    vector: list[float]
    limit: int = Field(10, ge=1, le=100)
    with_payload: bool = True

    @field_validator('vector')
    @classmethod
    def validate_search_vector(cls, v: list[float]) -> list[float]:
        if not v:
            raise ValueError("Search vector cannot be empty")

        if len(v) > 4096:
            raise ValueError(f"Vector dimension too large: {len(v)} (max: 4096)")

        # Check for NaN or Inf values
        for i, val in enumerate(v):
            if not isinstance(val, (int, float)):
                raise ValueError(f"Vector element at index {i} must be a number")
            if math.isnan(val):
                raise ValueError(f"Vector contains NaN at index {i}")
            if math.isinf(val):
                raise ValueError(f"Vector contains Inf at index {i}")

        return v


class DeleteRequest(BaseModel):
    collection: str
    ids: list[str | int]

