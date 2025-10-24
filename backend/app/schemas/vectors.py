from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class Point(BaseModel):
    id: str | int
    vector: list[float]
    payload: dict[str, Any] | None = None


class InsertVectorsRequest(BaseModel):
    collection: str = Field(..., min_length=1)
    points: list[Point] = Field(..., min_items=1)


class SearchRequest(BaseModel):
    collection: str
    vector: list[float]
    limit: int = Field(10, ge=1, le=100)
    with_payload: bool = True


class DeleteRequest(BaseModel):
    collection: str
    ids: list[str | int]

