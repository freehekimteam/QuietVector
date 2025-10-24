from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class OpEntry:
    id: str
    kind: str
    stage: str = "created"  # created|saving|uploading|verifying|completed|failed
    error: str | None = None
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())
    meta: dict[str, Any] = field(default_factory=dict)


class OpTracker:
    def __init__(self) -> None:
        self._ops: dict[str, OpEntry] = {}

    def create(self, kind: str, meta: dict[str, Any] | None = None) -> OpEntry:
        op_id = str(uuid.uuid4())
        entry = OpEntry(id=op_id, kind=kind, stage="created", meta=meta or {})
        self._ops[op_id] = entry
        return entry

    def update(self, op_id: str, *, stage: str | None = None, error: str | None = None, **kwargs: Any) -> OpEntry:
        e = self._ops.get(op_id)
        if not e:
            raise KeyError(op_id)
        if stage:
            e.stage = stage
        if error is not None:
            e.error = error
        if kwargs:
            e.meta.update(kwargs)
        e.updated_at = time.time()
        return e

    def get(self, op_id: str) -> OpEntry | None:
        return self._ops.get(op_id)

    def to_dict(self, op_id: str) -> dict[str, Any]:
        e = self.get(op_id)
        if not e:
            raise KeyError(op_id)
        return {
            "id": e.id,
            "kind": e.kind,
            "stage": e.stage,
            "error": e.error,
            "created_at": e.created_at,
            "updated_at": e.updated_at,
            "meta": e.meta,
        }


# Global tracker (in-memory)
tracker = OpTracker()

