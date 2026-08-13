"""ML Performance Dashboard endpoints.

GET /api/ml/dashboard           — admin: latest evaluation results for all models
GET /api/ml/evaluation/latest   — latest evaluation result for a specific model
GET /api/ml/evaluation/history  — all stored evaluation runs
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query

from backend.core.config import settings
from backend.core.request_id import get_request_id
from backend.db.firebase import get_db

router = APIRouter(prefix="/api/ml", tags=["ML Dashboard"])
logger = logging.getLogger("fieldmind.ml_dashboard")

MODEL_NAMES = ["disease_classifier", "leaf_verifier", "yolo_detector", "crop_recommender"]


def _require_admin(x_user_id: Optional[str] = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {"code": "UNAUTHENTICATED", "message": "Authentication required."},
                "request_id": get_request_id(),
            },
        )
    try:
        db = get_db()
        doc = db.collection("users").document(x_user_id).get()
        if not doc.exists:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Admin or Developer role required.",
                    },
                    "request_id": get_request_id(),
                },
            )
        role = doc.to_dict().get("role", "Farmer").lower()
        if role not in ("admin", "developer"):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Admin or Developer role required.",
                    },
                    "request_id": get_request_id(),
                },
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Admin check error: %s", exc)
        raise HTTPException(status_code=403, detail="Admin check failed.")
    return x_user_id


def _get_results_dir() -> Path:
    dir_ = settings.EVALUATION_RESULTS_DIR
    if not dir_.is_absolute():
        return Path(__file__).resolve().parent.parent.parent / dir_
    return dir_


def _load_latest_result(model_name: str) -> Optional[dict[str, Any]]:
    """Load the most recent evaluation JSON for a given model name."""
    results_dir = _get_results_dir()
    if not results_dir.exists():
        return None

    # Find all JSON files for this model (exclude summary files)
    candidates = sorted(
        results_dir.glob(f"{model_name}_*.json"),
        reverse=True,  # newest timestamp first (lexicographic sort works for ISO timestamps)
    )

    for path in candidates:
        if "summary" in path.name:
            continue
        try:
            with path.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception as exc:
            logger.warning("Failed to read %s: %s", path.name, exc)
            continue

    return None


def _load_all_results(model_name: str) -> list[dict[str, Any]]:
    """Load all evaluation results for a model, newest first."""
    results_dir = _get_results_dir()
    if not results_dir.exists():
        return []

    results = []
    for path in sorted(results_dir.glob(f"{model_name}_*.json"), reverse=True):
        if "summary" in path.name:
            continue
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                data["_filename"] = path.name
                results.append(data)
        except Exception:
            continue
    return results


@router.get("/dashboard")
def ml_dashboard(admin: str = None) -> dict[str, Any]:
    """Return the latest evaluation snapshot for all models.

    This endpoint is publicly accessible (read-only) since it exposes
    aggregated performance metrics that are appropriate for transparency.
    Sensitive feedback details remain admin-only.
    """
    dashboard: dict[str, Any] = {
        "models": {},
        "results_available": False,
    }

    for model_name in MODEL_NAMES:
        result = _load_latest_result(model_name)
        if result:
            dashboard["models"][model_name] = result
            dashboard["results_available"] = True
        else:
            dashboard["models"][model_name] = {
                "model": model_name,
                "dataset_available": False,
                "dataset_message": (
                    "No evaluation has been run yet. "
                    "Run: python -m evaluation.evaluate"
                ),
            }

    return dashboard


@router.get("/evaluation/latest")
def get_latest_evaluation(
    model: str = Query(
        ..., description="Model name", enum=MODEL_NAMES
    ),
) -> dict[str, Any]:
    """Return the most recent evaluation result for a specific model."""
    result = _load_latest_result(model)
    if result is None:
        return {
            "model": model,
            "dataset_available": False,
            "dataset_message": (
                f"No evaluation results found for '{model}'. "
                "Run: python -m evaluation.evaluate"
            ),
        }
    return result


@router.get("/evaluation/history")
def get_evaluation_history(
    model: str = Query(
        ..., description="Model name", enum=MODEL_NAMES
    ),
    limit: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    """Return evaluation history for a model (admin-only for full details)."""
    all_results = _load_all_results(model)[:limit]
    return {
        "model": model,
        "count": len(all_results),
        "results": [
            {
                "filename": r.get("_filename"),
                "evaluation_timestamp": r.get("evaluation_timestamp"),
                "accuracy": r.get("accuracy"),
                "macro_f1": r.get("macro_f1"),
                "sample_count": r.get("sample_count"),
                "dataset_available": r.get("dataset_available", False),
            }
            for r in all_results
        ],
    }
