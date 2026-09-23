"""Async inference worker for FieldMind.

This module handles the actual ML inference pipeline that runs inside an RQ
worker process (or synchronously when Redis is unavailable).

The pipeline:
    1. Image validation (blur, size, format)
    2. Leaf verification (ONNX)
    3. Disease classification (ONNX)
    4. Confidence analysis → confidence level
    5. YOLO severity / localisation (if high/medium confidence)
    6. Affected area estimation (bounding-box approximation)
    7. Persist diagnosis record to Firestore
    8. Mark job as completed

Entry points:
    run_inference_job(job_id, image_bytes, content_type, metadata)
        Called by the RQ worker OR synchronously by the API when Redis is off.
"""
from __future__ import annotations


import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from PIL import Image

from backend.core.config import settings

from backend.db.firebase import get_db
from backend.models.diagnosis_models import ConfidenceLevel, DiagnosisCreate
from backend.routers.diagnosis import save_diagnosis
from backend.services.image_validation import validate_image
from backend.services.leaf_verifier import LeafVerifier, LeafVerifierInferenceError
from backend.services.ml_inference import inference_service

logger = logging.getLogger("fieldmind.worker")


# ── Job store helpers ─────────────────────────────────────────────────────────


def _update_job(job_id: str, data: dict[str, Any]) -> None:
    try:
        db = get_db()
        data["updated_at"] = datetime.now(tz=timezone.utc).isoformat()
        db.collection("inference_jobs").document(job_id).update(data)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to update job", extra={"job_id": job_id, "error": str(exc)})


def create_job(
    user_id: Optional[str],
    plant_id: Optional[str],
    field_id: Optional[str],
    request_id: str,
) -> str:
    """Create an inference_jobs record and return the job_id."""
    db = get_db()
    job_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc).isoformat()
    db.collection("inference_jobs").document(job_id).set(
        {
            "job_id": job_id,
            "status": "queued",
            "user_id": user_id,
            "plant_id": plant_id,
            "field_id": field_id,
            "request_id": request_id,
            "created_at": now,
            "updated_at": now,
            "result": None,
            "error": None,
        }
    )
    return job_id


def get_job(job_id: str) -> Optional[dict[str, Any]]:
    db = get_db()
    doc = db.collection("inference_jobs").document(job_id).get()
    return doc.to_dict() if doc.exists else None


# ── Confidence categorisation ─────────────────────────────────────────────────


def _confidence_level(confidence: float) -> ConfidenceLevel:
    if confidence >= settings.DISEASE_HIGH_CONFIDENCE_THRESHOLD:
        return ConfidenceLevel.HIGH
    if confidence >= settings.DISEASE_MEDIUM_CONFIDENCE_THRESHOLD:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def _build_recommendation(
    disease_label: str,
    confidence_level: ConfidenceLevel,
    severity_detections: list[dict[str, Any]],
) -> str:
    if confidence_level == ConfidenceLevel.LOW:
        return (
            "FieldMind could not confidently identify this disease. "
            "Please upload a clearer image showing the affected area."
        )

    if confidence_level == ConfidenceLevel.MEDIUM:
        return (
            f"Tentative result: {disease_label}. "
            "Confidence is moderate — upload a clearer image for a definitive diagnosis."
        )

    # High confidence
    if not severity_detections:
        return (
            f"Detected {disease_label}. No severity regions localised — "
            "monitor the plant closely and consult local agronomy guidance."
        )

    top = max(severity_detections, key=lambda d: float(d.get("confidence", 0.0)))
    label = top.get("label", "the affected area")
    return (
        f"Detected {disease_label}. Affected area: {label}. "
        "Apply appropriate treatment based on local agronomy guidance."
    )


# ── Main pipeline ─────────────────────────────────────────────────────────────


def run_inference_job(
    job_id: str,
    image_bytes: bytes,
    content_type: Optional[str],
    filename: Optional[str],
    user_id: Optional[str],
    plant_id: Optional[str],
    field_id: Optional[str],
    leaf_verifier: Optional[LeafVerifier] = None,
) -> dict[str, Any]:
    """Execute the full inference pipeline for a given job.

    This function is safe to call:
    - Synchronously (returns result dict immediately)
    - As an RQ job (called by the worker process)

    The job document in Firestore is updated at each pipeline stage so the
    frontend can display meaningful progress even when polling.

    Args:
        job_id:       Pre-created job identifier.
        image_bytes:  Raw uploaded image bytes.
        content_type: MIME type string or None.
        filename:     Original filename or None.
        user_id:      Authenticated user UID (or None for anonymous).
        plant_id:     Optional plant tracking identifier.
        field_id:     Optional field tracking identifier.
        leaf_verifier: Loaded LeafVerifier instance (injected to avoid
                       reloading inside the worker).

    Returns:
        The completed result dict (also stored in Firestore).
    """
    pipeline_start = time.perf_counter()
    logger.info(
        "Inference job started",
        extra={"job_id": job_id, "user_id": user_id},
    )

    try:
        # ── Stage 1: Image validation ─────────────────────────────────
        _update_job(job_id, {"status": "processing", "stage": "validating_image"})

        validation = validate_image(image_bytes, content_type, filename)
        if not validation.passed:
            result = {
                "success": False,
                "stage_failed": "image_validation",
                "error_code": validation.error_code,
                "user_message": validation.user_message,
                "details": validation.details,
            }
            _update_job(
                job_id, {"status": "failed", "result": result, "error": validation.error_code}
            )
            return result

        image: Image.Image = validation.image  # type: ignore[assignment]

        # ── Stage 2: Leaf verification ────────────────────────────────
        _update_job(job_id, {"stage": "verifying_leaf"})

        if leaf_verifier is None:
            logger.warning("Leaf verifier not provided to worker; skipping verification.")
            verification_result = {
                "verification": {
                    "is_leaf": True,
                    "status": "skipped",
                    "confidence": 1.0,
                    "predicted_class": "leaf",
                },
                "pipeline": {"allow_processing": True, "next_step": "disease_detection"},
            }
        else:
            try:
                verification_result = leaf_verifier.predict(image)
            except LeafVerifierInferenceError as exc:
                result = {
                    "success": False,
                    "stage_failed": "leaf_verification",
                    "error_code": "LEAF_VERIFICATION_FAILED",
                    "user_message": "Could not verify the leaf. Please try again.",
                }
                _update_job(job_id, {"status": "failed", "result": result, "error": str(exc)})
                return result

        verification = verification_result["verification"]
        pipeline_ctrl = verification_result["pipeline"]

        if not pipeline_ctrl["allow_processing"]:
            result = {
                "success": True,
                "stage_failed": None,
                "verification": verification,
                "pipeline": pipeline_ctrl,
                "status": "rejected",
                "user_message": verification_result.get(
                    "message",
                    "Please upload a clear image of a single plant leaf.",
                ),
            }
            _update_job(job_id, {"status": "completed", "result": result})
            return result

        # ── Stage 3: Disease classification ──────────────────────────
        _update_job(job_id, {"stage": "classifying_disease"})

        disease_label, disease_confidence, probs = inference_service.run_classifier(image)
        conf_level = _confidence_level(disease_confidence)
        top_k = inference_service.get_top_k_predictions(probs, k=3)

        logger.info(
            "Disease classified",
            extra={
                "job_id": job_id,
                "disease": disease_label,
                "confidence": round(disease_confidence, 4),
                "confidence_level": conf_level.value,
            },
        )

        # ── Stage 4: YOLO severity (only for high/medium confidence) ──
        severity_detections: list[dict[str, Any]] = []
        affected_area_pct: Optional[float] = None

        if conf_level in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM):
            _update_job(job_id, {"stage": "analysing_severity"})
            try:
                severity_detections = inference_service.run_yolo(image)
                affected_area_pct = inference_service.compute_affected_area_pct(
                    severity_detections, image.size
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "YOLO failed — continuing without severity",
                    extra={"job_id": job_id, "error": str(exc)},
                )
        else:
            logger.info(
                "YOLO skipped: low confidence",
                extra={"job_id": job_id, "confidence_level": conf_level.value},
            )

        # ── Stage 5: Build result ─────────────────────────────────────
        recommendation = _build_recommendation(
            disease_label, conf_level, severity_detections
        )

        # Parse crop from disease label (format: "crop_condition")
        crop: Optional[str] = None
        if "_" in disease_label:
            crop = disease_label.split("_")[0].capitalize()

        # ── Stage 6: Persist diagnosis ────────────────────────────────
        diagnosis_id: Optional[str] = None
        if user_id:
            try:
                image_ref = str(uuid.uuid4())  # Reference UUID (no binary stored)
                diag = DiagnosisCreate(
                    user_id=user_id,
                    crop=crop,
                    predicted_disease=disease_label,
                    confidence=disease_confidence,
                    confidence_level=conf_level,
                    severity_detections=severity_detections,
                    affected_area_pct=affected_area_pct,
                    model_name=inference_service.classifier_model_name,
                    model_version=inference_service.classifier_model_version,
                    recommendation=recommendation,
                    image_reference=image_ref,
                    blur_score=validation.blur_score,
                    plant_id=plant_id,
                    field_id=field_id,
                )
                diagnosis_id = save_diagnosis(diag)
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Failed to persist diagnosis",
                    extra={"job_id": job_id, "error": str(exc)},
                )

        elapsed_ms = round((time.perf_counter() - pipeline_start) * 1000, 1)

        result = {
            "success": True,
            "stage_failed": None,
            "job_id": job_id,
            "diagnosis_id": diagnosis_id,
            "verification": verification,
            "pipeline": pipeline_ctrl,
            "status": "ok" if conf_level != ConfidenceLevel.LOW else "uncertain",
            "disease": disease_label,
            "confidence": disease_confidence,
            "confidence_level": conf_level.value,
            "top_predictions": top_k,
            "crop": crop,
            "disease_prediction": {
                "label": disease_label,
                "confidence": disease_confidence,
                "confidence_level": conf_level.value,
            },
            "severity": {
                "detections": severity_detections,
                "bounding_boxes": [d.get("box", []) for d in severity_detections],
                "affected_area_pct": affected_area_pct,
                "area_pct_note": (
                    "Bounding-box approximation; may overestimate true affected area."
                    if affected_area_pct is not None
                    else None
                ),
            },
            "recommendation": recommendation,
            "image_quality": {
                "blur_score": validation.blur_score,
                "width": validation.details.get("width"),
                "height": validation.details.get("height"),
            },
            "latency_ms": elapsed_ms,
        }

        if conf_level == ConfidenceLevel.LOW:
            result["user_message"] = (
                "FieldMind could not confidently identify this disease. "
                "Please upload a clearer image showing the affected area."
            )

        _update_job(job_id, {"status": "completed", "result": result})

        logger.info(
            "Inference job completed",
            extra={
                "job_id": job_id,
                "latency_ms": elapsed_ms,
                "disease": disease_label,
                "confidence": round(disease_confidence, 4),
            },
        )

        return result

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Inference job failed unexpectedly",
            extra={"job_id": job_id, "error": str(exc)},
            exc_info=True,
        )
        error_result = {
            "success": False,
            "stage_failed": "unknown",
            "error_code": "INFERENCE_FAILED",
            "user_message": "Disease analysis could not be completed. Please try again.",
        }
        try:
            _update_job(
                job_id,
                {"status": "failed", "result": error_result, "error": str(exc)},
            )
        except Exception:  # noqa: BLE001
            pass
        return error_result
