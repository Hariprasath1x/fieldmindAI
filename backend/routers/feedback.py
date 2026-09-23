"""Prediction feedback router.

POST /api/feedback                — authenticated users submit feedback
GET  /api/feedback/dashboard      — admin-only feedback analytics
"""
from __future__ import annotations

import logging
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from backend.core.request_id import get_request_id
from backend.db.firebase import get_db
from backend.models.diagnosis_models import (
    FeedbackCreate,
    FeedbackDashboardResponse,
    FeedbackRecord,
    FeedbackType,
)

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])
logger = logging.getLogger("fieldmind.feedback")


def _require_uid(x_user_id: Optional[str] = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {"code": "UNAUTHENTICATED", "message": "Authentication required."},
                "request_id": get_request_id(),
            },
        )
    return x_user_id


def _require_admin(x_user_id: Optional[str] = Header(None)) -> str:
    """Check that the caller is an admin.

    Admin status is stored in the `users` Firestore collection as
    ``role == "admin"``.  Falls back gracefully when Firestore is unavailable.
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        db = get_db()
        doc = db.collection("users").document(x_user_id).get()
        if not doc.exists:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Admin access required.",
                    },
                    "request_id": get_request_id(),
                },
            )
        data = doc.to_dict()
        role = data.get("role", "Farmer")
        if role.lower() not in ("admin", "developer"):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "Admin access required.",
                    },
                    "request_id": get_request_id(),
                },
            )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("Admin check failed — denying access", extra={"error": str(exc)})
        raise HTTPException(status_code=403, detail="Admin check failed.")

    return x_user_id


def _get_firestore():
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")
    return db


@router.post("", response_model=FeedbackRecord, status_code=201)
def submit_feedback(
    payload: FeedbackCreate,
    uid: str = Depends(_require_uid),
    db=Depends(_get_firestore),
) -> FeedbackRecord:
    """Submit correctness feedback for a prediction.

    The prediction_id must match a diagnosis accessible to this user.
    """
    # Validate ownership of the prediction
    diag_doc = db.collection("diagnoses").document(payload.prediction_id).get()
    if diag_doc.exists:
        diag_data = diag_doc.to_dict()
        if diag_data.get("user_id") != uid:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": {
                        "code": "FORBIDDEN",
                        "message": "You can only submit feedback for your own predictions.",
                    },
                    "request_id": get_request_id(),
                },
            )

    # Enforce that user_id in the payload matches the authenticated uid
    if payload.user_id != uid:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "USER_ID_MISMATCH",
                    "message": "Payload user_id must match authenticated user.",
                },
                "request_id": get_request_id(),
            },
        )

    feedback_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc).isoformat()

    record = FeedbackRecord(
        feedback_id=feedback_id,
        timestamp=now,
        **payload.model_dump(),
    )

    db.collection("prediction_feedback").document(feedback_id).set(record.model_dump())

    logger.info(
        "Feedback submitted",
        extra={
            "feedback_id": feedback_id,
            "prediction_id": payload.prediction_id,
            "feedback_type": payload.feedback_type.value,
            "user_id": uid,
        },
    )

    return record


@router.get("/dashboard", response_model=FeedbackDashboardResponse)
def feedback_dashboard(
    model_name: Optional[str] = Query(default=None),
    admin_uid: str = Depends(_require_admin),
    db=Depends(_get_firestore),
) -> FeedbackDashboardResponse:
    """Admin-only view: aggregated feedback analytics."""
    all_feedback = [d.to_dict() for d in db.collection("prediction_feedback").stream()]
    all_diagnoses = [d.to_dict() for d in db.collection("diagnoses").stream()]

    if model_name:
        relevant_diag_ids = {
            d["diagnosis_id"]
            for d in all_diagnoses
            if d.get("model_name") == model_name
        }
        all_feedback = [
            f for f in all_feedback if f.get("prediction_id") in relevant_diag_ids
        ]

    total_predictions = len(all_diagnoses)
    feedback_received = len(all_feedback)
    feedback_rate = (
        round(feedback_received / total_predictions * 100, 1)
        if total_predictions > 0
        else 0.0
    )

    correct_count = sum(
        1 for f in all_feedback if f.get("feedback_type") == FeedbackType.CORRECT.value
    )
    incorrect_count = feedback_received - correct_count

    # Incorrect by class
    incorrect_by_class: dict[str, int] = Counter(
        f.get("predicted_label", "unknown")
        for f in all_feedback
        if f.get("feedback_type") == FeedbackType.INCORRECT.value
    )

    # Confusion pairs: predicted → actual
    confusion_counter: dict[tuple[str, str], int] = defaultdict(int)
    for f in all_feedback:
        if f.get("feedback_type") == FeedbackType.INCORRECT.value:
            predicted = f.get("predicted_label", "unknown")
            actual = f.get("actual_label") or "not_specified"
            confusion_counter[(predicted, actual)] += 1

    confusion_pairs = [
        {"predicted": p, "actual": a, "count": c}
        for (p, a), c in sorted(confusion_counter.items(), key=lambda x: -x[1])
    ]

    return FeedbackDashboardResponse(
        total_predictions=total_predictions,
        feedback_received=feedback_received,
        feedback_rate_pct=feedback_rate,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        incorrect_by_class=dict(incorrect_by_class),
        confusion_pairs=confusion_pairs,
    )
