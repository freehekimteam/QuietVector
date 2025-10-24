from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


Distance = Literal["Cosine", "Dot", "Euclid"]


class CreateCollectionRequest(BaseModel):
    name: str = Field(..., min_length=1)
    vectors_size: int = Field(..., ge=1)
    distance: Distance = Field("Cosine")
    # Optional HNSW params
    ef_construct: Optional[int] = Field(None, ge=4, le=4096)
    m: Optional[int] = Field(None, ge=4, le=128)


class CollectionInfo(BaseModel):
    name: str
    points_count: int
    vectors_count: int
    status: str

