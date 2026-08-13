"""Health and readiness endpoints for FieldMind.

GET /health   — liveness probe (is the process alive?)
GET /ready    — readiness probe (are all dependencies available?)
GET /metrics  — application metrics summary
"""
from __future__ import annotations

import logging

from typing import Any

from fastapi import APIRouter, Request

from backend.core.config import settings
from backend.db.firebase import get_db

router = APIRouter(tags=["Health"])
logger = logging.getLogger("fieldmind.health")

# In-memory counters (reset on restart — suitable for single-process dev)
_metrics: dict[str, Any] = {
    "api_requests_total": 0,
    "api_errors_total": 0,
    "inference_requests_total": 0,
    "inference_errors_total": 0,
    "inference_latency_ms_sum": 0.0,
    "inference_latency_ms_count": 0,
    "leaf_verifications_total": 0,
    "leaf_rejections_total": 0,
}


def increment(key: str, value: float = 1.0) -> None:
    """Thread-safe increment of a metric counter."""
    _metrics[key] = _metrics.get(key, 0) + value


@router.get("/health", tags=["Health"])
def health() -> dict[str, str]:
    """Liveness probe — confirms the process is running."""
    return {"status": "ok", "service": "fieldmind-api"}


@router.get("/ready", tags=["Health"])
def ready(request: Request) -> dict[str, Any]:
    """Readiness probe — checks all dependencies are available."""
    checks: dict[str, str] = {}
    overall_ready = True

    # ── ML models ─────────────────────────────────────────────────────
    ml_service = getattr(request.app.state, "ml_service", None)
    leaf_verifier = getattr(request.app.state, "leaf_verifier", None)

    if ml_service and ml_service.is_ready:
        checks["ml_models"] = "ready"
    else:
        checks["ml_models"] = "not_ready"
        overall_ready = False

    if leaf_verifier is not None:
        checks["leaf_verifier"] = "ready"
    else:
        checks["leaf_verifier"] = "not_ready"
        # Leaf verifier not being ready degrades but doesn't block
        # (inference still works, verification is skipped)

    # ── Database ──────────────────────────────────────────────────────
    try:
        db = get_db()
        # Lightweight probe: attempt a .collection() call
        db.collection("_health_check")
        checks["database"] = "ready"
    except Exception as exc:
        checks["database"] = f"degraded: {exc}"
        overall_ready = False

    # ── Redis (optional) ──────────────────────────────────────────────
    if settings.ASYNC_INFERENCE_ENABLED:
        try:
            from redis import Redis  # type: ignore

            r = Redis.from_url(settings.REDIS_URL, socket_timeout=1)
            r.ping()
            checks["redis"] = "ready"
        except Exception as exc:
            checks["redis"] = f"unavailable: {exc}"
            overall_ready = False
    else:
        checks["redis"] = "not_configured"

    status_code = 200 if overall_ready else 503
    response = {
        "status": "ready" if overall_ready else "degraded",
        "checks": checks,
    }

    return response


@router.get("/metrics", tags=["Health"])
def metrics() -> dict[str, Any]:
    """Application metrics summary."""
    avg_latency = (
        _metrics["inference_latency_ms_sum"] / _metrics["inference_latency_ms_count"]
        if _metrics["inference_latency_ms_count"] > 0
        else None
    )

    return {
        "api_requests_total": _metrics["api_requests_total"],
        "api_errors_total": _metrics["api_errors_total"],
        "inference_requests_total": _metrics["inference_requests_total"],
        "inference_errors_total": _metrics["inference_errors_total"],
        "inference_avg_latency_ms": (
            round(avg_latency, 1) if avg_latency is not None else None
        ),
        "leaf_verifications_total": _metrics["leaf_verifications_total"],
        "leaf_rejections_total": _metrics["leaf_rejections_total"],
    }
