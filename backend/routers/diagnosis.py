"""Diagnosis history and progression router.

Endpoints
---------
GET  /api/diagnosis/history          — authenticated user's diagnosis history
GET  /api/diagnosis/{id}             — single diagnosis record
POST /api/diagnosis/{id}/feedback    — submit prediction feedback
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from backend.core.request_id import get_request_id
from backend.db.firebase import get_db
from backend.models.diagnosis_models import (
    DiagnosisCreate,
    DiagnosisHistoryResponse,
    DiagnosisResponse,
    ProgressionPoint,
    ProgressionStatus,
    ProgressionSummary,
)

router = APIRouter(prefix="/api/diagnosis", tags=["Diagnosis"])
logger = logging.getLogger("fieldmind.diagnosis")


# ── Auth helper ───────────────────────────────────────────────────────────────


def _require_uid(x_user_id: Optional[str] = Header(None)) -> str:
    """Extract authenticated user ID from the X-User-ID header.

    The React frontend sets this header from the Firebase Auth token uid.
    In production, this should be validated against a Firebase token; here we
    accept the header value directly (same pattern used by the existing
    marketplace endpoints).
    """
    if not x_user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "UNAUTHENTICATED",
                    "message": "Authentication required.",
                },
                "request_id": get_request_id(),
            },
        )
    return x_user_id


def _get_firestore():
    db = get_db()
    if db is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Database is temporarily unavailable.",
                },
                "request_id": get_request_id(),
            },
        )
    return db


# ── Persistence helpers ───────────────────────────────────────────────────────


def save_diagnosis(diagnosis: DiagnosisCreate) -> str:
    """Persist a diagnosis record and return its ID."""
    db = get_db()
    diagnosis_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc).isoformat()

    data: dict[str, Any] = {
        "diagnosis_id": diagnosis_id,
        "timestamp": now,
        "status": "completed",
        **diagnosis.model_dump(),
    }

    db.collection("diagnoses").document(diagnosis_id).set(data)
    logger.info(
        "Diagnosis saved",
        extra={
            "diagnosis_id": diagnosis_id,
            "user_id": diagnosis.user_id,
            "disease": diagnosis.predicted_disease,
            "confidence": round(diagnosis.confidence, 4),
            "request_id": get_request_id(),
        },
    )
    return diagnosis_id


# ── Progression logic ─────────────────────────────────────────────────────────


def _compute_progression(
    records: list[dict[str, Any]],
) -> ProgressionSummary | None:
    """Compute disease progression across multiple diagnosis records.

    Requires at least 2 records for the same plant_id.
    Progression is based on affected_area_pct where available, otherwise
    confidence trend is used as a proxy.
    """
    if len(records) < 2:
        return None

    plant_id = records[0].get("plant_id", "unknown")
    sorted_records = sorted(records, key=lambda r: r.get("timestamp", ""))

    points = [
        ProgressionPoint(
            diagnosis_id=r.get("diagnosis_id", ""),
            timestamp=r.get("timestamp", ""),
            predicted_disease=r.get("predicted_disease", "unknown"),
            confidence=float(r.get("confidence", 0.0)),
            affected_area_pct=r.get("affected_area_pct"),
        )
        for r in sorted_records
    ]

    # Use affected_area_pct if available in both first and last records
    first_area = points[0].affected_area_pct
    last_area = points[-1].affected_area_pct
    area_delta: Optional[float] = None
    status: ProgressionStatus
    message: str

    if first_area is not None and last_area is not None:
        area_delta = round(last_area - first_area, 2)
        if area_delta > 2.0:
            status = ProgressionStatus.WORSENING
            message = (
                f"Affected area increased from {first_area:.1f}% to {last_area:.1f}% "
                f"(+{area_delta:.1f} percentage points). Immediate treatment recommended."
            )
        elif area_delta < -2.0:
            status = ProgressionStatus.IMPROVING
            message = (
                f"Affected area decreased from {first_area:.1f}% to {last_area:.1f}% "
                f"({area_delta:.1f} percentage points). Treatment appears effective."
            )
        else:
            status = ProgressionStatus.STABLE
            message = f"Affected area is stable at approximately {last_area:.1f}%."
    else:
        # Fallback: use confidence trend as proxy
        first_conf = points[0].confidence
        last_conf = points[-1].confidence
        conf_delta = last_conf - first_conf

        if len(records) == 1:
            status = ProgressionStatus.NEW
            message = "First diagnosis for this plant."
        elif abs(conf_delta) < 0.05:
            status = ProgressionStatus.STABLE
            message = "Disease appears stable based on consecutive diagnoses."
        elif conf_delta > 0.05:
            status = ProgressionStatus.WORSENING
            message = "Disease confidence increasing — consider treatment."
        else:
            status = ProgressionStatus.IMPROVING
            message = "Disease confidence decreasing — condition may be improving."

    return ProgressionSummary(
        plant_id=plant_id,
        points=points,
        latest_status=status,
        area_delta_pct=area_delta,
        message=message,
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/history", response_model=DiagnosisHistoryResponse)
def get_diagnosis_history(
    limit: int = Query(default=20, ge=1, le=100),
    plant_id: Optional[str] = Query(default=None),
    uid: str = Depends(_require_uid),
    db=Depends(_get_firestore),
) -> DiagnosisHistoryResponse:
    """Return the authenticated user's diagnosis history, newest first."""
    try:
        col = db.collection("diagnoses").where("user_id", "==", uid)
        docs = list(col.stream())
    except Exception as exc:
        logger.error(
            "Failed to fetch diagnosis history",
            extra={"user_id": uid, "error": str(exc)},
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {"code": "DB_ERROR", "message": "Failed to fetch history."},
                "request_id": get_request_id(),
            },
        ) from exc

    records = [d.to_dict() for d in docs]

    # Filter by plant_id if requested
    if plant_id:
        records = [r for r in records if r.get("plant_id") == plant_id]

    # Sort newest first in Python (Firestore mock doesn't support order_by)
    records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    records = records[:limit]

    diagnoses = []
    for r in records:
        # Compute progression if plant_id is present
        progression = None
        pid = r.get("plant_id")
        if pid:
            siblings = [d for d in records if d.get("plant_id") == pid]
            prog = _compute_progression(siblings)
            if prog:
                progression = prog.model_dump()

        diagnoses.append(
            DiagnosisResponse(
                **{k: v for k, v in r.items() if k != "progression"},
                progression=progression,
            )
        )

    return DiagnosisHistoryResponse(diagnoses=diagnoses, total=len(diagnoses))


@router.get("/{diagnosis_id}", response_model=DiagnosisResponse)
def get_diagnosis(
    diagnosis_id: str,
    uid: str = Depends(_require_uid),
    db=Depends(_get_firestore),
) -> DiagnosisResponse:
    """Return a single diagnosis record (owner-only)."""
    doc = db.collection("diagnoses").document(diagnosis_id).get()

    if not doc.exists:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"code": "NOT_FOUND", "message": "Diagnosis not found."},
                "request_id": get_request_id(),
            },
        )

    data = doc.to_dict()

    # Authorization: only the owning user may read their own diagnoses
    if data.get("user_id") != uid:
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You do not have access to this diagnosis.",
                },
                "request_id": get_request_id(),
            },
        )

    return DiagnosisResponse(**data)


@router.get("/{diagnosis_id}/progression")
def get_plant_progression(
    diagnosis_id: str,
    uid: str = Depends(_require_uid),
    db=Depends(_get_firestore),
) -> dict:
    """Return progression data for the plant associated with a diagnosis."""
    doc = db.collection("diagnoses").document(diagnosis_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Diagnosis not found.")

    data = doc.to_dict()
    if data.get("user_id") != uid:
        raise HTTPException(status_code=403, detail="Forbidden.")

    plant_id = data.get("plant_id")
    if not plant_id:
        return {"message": "No plant_id associated with this diagnosis.", "points": []}

    # Fetch all records for this plant
    siblings = list(
        db.collection("diagnoses")
        .where("user_id", "==", uid)
        .where("plant_id", "==", plant_id)
        .stream()
    )
    records = [s.to_dict() for s in siblings]
    records.sort(key=lambda r: r.get("timestamp", ""))

    prog = _compute_progression(records)
    if not prog:
        return {"message": "Not enough data for progression analysis.", "points": []}

    return prog.model_dump()
