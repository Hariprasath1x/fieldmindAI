"""Async inference submission and status endpoints.

POST /api/inference/submit      — upload image → get job_id (runs sync or async)
GET  /api/inference/{job_id}    — poll job status and result
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, Header, HTTPException, Request, UploadFile

from backend.core.config import settings
from backend.core.request_id import get_request_id
from backend.models.diagnosis_models import (
    InferenceJobResponse,
    InferenceJobStatusResponse,
    JobStatus,
)
from backend.worker.inference_worker import create_job, get_job, run_inference_job

router = APIRouter(prefix="/api/inference", tags=["Inference"])
logger = logging.getLogger("fieldmind.inference")


def _get_leaf_verifier(request: Request):
    return getattr(request.app.state, "leaf_verifier", None)


@router.post("/submit", response_model=InferenceJobResponse)
async def submit_inference(
    request: Request,
    file: UploadFile = File(...),
    plant_id: Optional[str] = Form(default=None),
    field_id: Optional[str] = Form(default=None),
    x_user_id: Optional[str] = Header(default=None),
) -> InferenceJobResponse:
    """Submit an image for disease analysis.

    Returns a job_id immediately.  Poll ``GET /api/inference/{job_id}`` for
    the result.  When Redis is not configured the inference runs synchronously
    before the response is returned (the status will be 'completed' instantly).
    """
    request_id = get_request_id()

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_FILE_TYPE",
                    "message": "Please upload an image file.",
                },
                "request_id": request_id,
            },
        )

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {"code": "EMPTY_FILE", "message": "Uploaded file is empty."},
                "request_id": request_id,
            },
        )

    # Create the job record
    job_id = create_job(
        user_id=x_user_id,
        plant_id=plant_id,
        field_id=field_id,
        request_id=request_id,
    )

    logger.info(
        "Inference job created",
        extra={
            "job_id": job_id,
            "user_id": x_user_id,
            "file_name": file.filename,
            "content_type": file.content_type,
            "request_id": request_id,
        },
    )

    leaf_verifier = _get_leaf_verifier(request)

    if settings.ASYNC_INFERENCE_ENABLED:
        # Attempt to enqueue via Redis Queue
        try:
            from redis import Redis  # type: ignore
            from rq import Queue  # type: ignore

            redis_conn = Redis.from_url(settings.REDIS_URL)
            q = Queue("inference", connection=redis_conn)
            q.enqueue(
                run_inference_job,
                job_id=job_id,
                image_bytes=image_bytes,
                content_type=file.content_type,
                filename=file.filename,
                user_id=x_user_id,
                plant_id=plant_id,
                field_id=field_id,
                leaf_verifier=None,  # Worker will load its own verifier
                job_timeout=settings.JOB_TIMEOUT_SECONDS,
            )
            logger.info("Job enqueued to Redis", extra={"job_id": job_id})
            return InferenceJobResponse(
                job_id=job_id, status=JobStatus.QUEUED, request_id=request_id
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Redis unavailable — falling back to sync inference",
                extra={"error": str(exc), "job_id": job_id},
            )

    # Synchronous fallback (runs in a thread pool to avoid blocking the event loop)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        None,
        lambda: run_inference_job(
            job_id=job_id,
            image_bytes=image_bytes,
            content_type=file.content_type,
            filename=file.filename,
            user_id=x_user_id,
            plant_id=plant_id,
            field_id=field_id,
            leaf_verifier=leaf_verifier,
        ),
    )

    return InferenceJobResponse(
        job_id=job_id, status=JobStatus.COMPLETED, request_id=request_id
    )


@router.get("/{job_id}", response_model=InferenceJobStatusResponse)
def get_inference_status(
    job_id: str,
    x_user_id: Optional[str] = Header(default=None),
) -> InferenceJobStatusResponse:
    """Poll the status of an inference job."""
    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"code": "JOB_NOT_FOUND", "message": "Inference job not found."},
                "request_id": get_request_id(),
            },
        )

    # Security: users can only see their own jobs (when authenticated)
    if x_user_id and job.get("user_id") and job["user_id"] != x_user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": {"code": "FORBIDDEN", "message": "Access denied."},
                "request_id": get_request_id(),
            },
        )

    return InferenceJobStatusResponse(
        job_id=job["job_id"],
        status=JobStatus(job.get("status", "queued")),
        result=job.get("result"),
        error=job.get("error"),
        created_at=job.get("created_at", ""),
        updated_at=job.get("updated_at", ""),
    )
