"""
QuietVector API
Sade, güvenli Qdrant yönetim arayüzünün FastAPI backend'i.
"""
from __future__ import annotations

import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="QuietVector API", version="0.1.0")

# Metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health")
def health():
    return {"status": "ok"}

