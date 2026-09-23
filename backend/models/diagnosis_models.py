"""Pydantic models for diagnosis persistence and prediction feedback."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, ConfigDict


# ── Enums ─────────────────────────────────────────────────────────────────────


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProgressionStatus(str, Enum):
    NEW = "new"
    IMPROVING = "improving"
    STABLE = "stable"
    WORSENING = "worsening"


class FeedbackType(str, Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Diagnosis models ──────────────────────────────────────────────────────────


class DiagnosisCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    user_id: str
    crop: Optional[str] = None
    predicted_disease: str
    confidence: float
    confidence_level: ConfidenceLevel
    severity_detections: list[dict[str, Any]] = Field(default_factory=list)
    affected_area_pct: Optional[float] = None  # bbox approximation, may be None
    model_name: str
    model_version: str = "1.0.0"
    recommendation: str
    image_reference: Optional[str] = None   # UUID or storage path
    blur_score: Optional[float] = None
    plant_id: Optional[str] = None          # Optional grouping identifier
    field_id: Optional[str] = None          # Optional field grouping


class DiagnosisRecord(DiagnosisCreate):
    diagnosis_id: str
    timestamp: str  # ISO 8601
    status: str = "completed"


class DiagnosisResponse(BaseModel):
    diagnosis_id: str
    user_id: str
    crop: Optional[str] = None
    predicted_disease: str
    confidence: float
    confidence_level: str
    severity_detections: list[dict[str, Any]] = Field(default_factory=list)
    affected_area_pct: Optional[float] = None
    model_name: str
    model_version: str
    recommendation: str
    image_reference: Optional[str] = None
    blur_score: Optional[float] = None
    plant_id: Optional[str] = None
    field_id: Optional[str] = None
    timestamp: str
    status: str
    progression: Optional[dict[str, Any]] = None


class DiagnosisHistoryResponse(BaseModel):
    diagnoses: list[DiagnosisResponse]
    total: int


# ── Progression ───────────────────────────────────────────────────────────────


class ProgressionPoint(BaseModel):
    diagnosis_id: str
    timestamp: str
    predicted_disease: str
    confidence: float
    affected_area_pct: Optional[float] = None


class ProgressionSummary(BaseModel):
    plant_id: str
    points: list[ProgressionPoint]
    latest_status: ProgressionStatus
    area_delta_pct: Optional[float] = None
    message: str


# ── Inference job models ──────────────────────────────────────────────────────


class InferenceJobCreate(BaseModel):
    user_id: Optional[str] = None
    plant_id: Optional[str] = None
    field_id: Optional[str] = None


class InferenceJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    request_id: str


class InferenceJobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str


# ── Feedback models ───────────────────────────────────────────────────────────


class FeedbackCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    prediction_id: str
    user_id: str
    predicted_label: str
    actual_label: Optional[str] = None
    feedback_type: FeedbackType
    notes: Optional[str] = None


class FeedbackRecord(FeedbackCreate):
    feedback_id: str
    timestamp: str


class FeedbackDashboardResponse(BaseModel):
    total_predictions: int
    feedback_received: int
    feedback_rate_pct: float
    correct_count: int
    incorrect_count: int
    incorrect_by_class: dict[str, int]
    confusion_pairs: list[dict[str, Any]]  # [{predicted, actual, count}]
