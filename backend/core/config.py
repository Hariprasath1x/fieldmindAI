"""Centralised application configuration for FieldMind.

All tuneable values are read from environment variables so that nothing is
hard-coded in the source tree.  A `.env.example` file at the project root
documents every variable with a safe placeholder value.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


def _env_float(key: str, default: float) -> float:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_str(key: str, default: str) -> str:
    return os.getenv(key, default)


def _env_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes"}


class Settings:
    """Application-wide settings resolved once at import time."""

    # --- Environment ---
    ENVIRONMENT: str = _env_str("FIELDMIND_ENV", "development")
    LOG_LEVEL: str = _env_str("LOG_LEVEL", "INFO")

    # --- API ---
    API_HOST: str = _env_str("API_HOST", "0.0.0.0")
    API_PORT: int = _env_int("API_PORT", 8002)
    CORS_ORIGIN_REGEX: str = _env_str(
        "CORS_ORIGIN_REGEX",
        r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    )

    # --- Model paths ---
    MODELS_DIR: Path = Path(_env_str("MODELS_DIR", "models"))

    # --- Leaf verification thresholds ---
    # Confidence below which the verifier returns "uncertain" (no leaf or not sure)
    LEAF_VERIFICATION_THRESHOLD: float = _env_float(
        "LEAF_VERIFICATION_THRESHOLD", 0.85
    )

    # --- Disease classification thresholds ---
    # Confidence >= HIGH → full diagnosis + YOLO
    DISEASE_HIGH_CONFIDENCE_THRESHOLD: float = _env_float(
        "DISEASE_HIGH_CONFIDENCE_THRESHOLD", 0.75
    )
    # Confidence between MEDIUM and HIGH → tentative result, warn user
    DISEASE_MEDIUM_CONFIDENCE_THRESHOLD: float = _env_float(
        "DISEASE_MEDIUM_CONFIDENCE_THRESHOLD", 0.45
    )
    # Below MEDIUM → no definitive diagnosis

    # --- YOLO ---
    # Detection confidence gate inside YOLO post-processing
    YOLO_CONFIDENCE_THRESHOLD: float = _env_float("YOLO_CONFIDENCE_THRESHOLD", 0.25)
    YOLO_IOU_THRESHOLD: float = _env_float("YOLO_IOU_THRESHOLD", 0.45)

    # --- Image quality thresholds ---
    # Laplacian variance below this → image considered too blurry
    IMAGE_BLUR_THRESHOLD: float = _env_float("IMAGE_BLUR_THRESHOLD", 100.0)
    # Maximum upload size in MB
    MAX_IMAGE_SIZE_MB: float = _env_float("MAX_IMAGE_SIZE_MB", 10.0)
    # Minimum acceptable dimension in pixels (width or height)
    MIN_IMAGE_DIMENSION_PX: int = _env_int("MIN_IMAGE_DIMENSION_PX", 64)
    # Minimum dimension for reliable ML inference
    RECOMMENDED_MIN_IMAGE_DIMENSION_PX: int = _env_int(
        "RECOMMENDED_MIN_IMAGE_DIMENSION_PX", 224
    )

    # --- Inference job ---
    # Seconds after which a job is considered stale / timed-out
    JOB_TIMEOUT_SECONDS: int = _env_int("JOB_TIMEOUT_SECONDS", 120)
    # Whether to use async queue (requires Redis); falls back to sync when False
    ASYNC_INFERENCE_ENABLED: bool = _env_bool("ASYNC_INFERENCE_ENABLED", False)

    # --- Redis ---
    REDIS_URL: str = _env_str("REDIS_URL", "redis://localhost:6379/0")

    # --- Firebase ---
    FIREBASE_CREDENTIALS_PATH: str = _env_str(
        "FIREBASE_CREDENTIALS_PATH",
        "backend/firebase_service_account.json",
    )

    # --- Evaluation ---
    EVALUATION_RESULTS_DIR: Path = Path(
        _env_str("EVALUATION_RESULTS_DIR", "evaluation/results")
    )

    # Derived helpers
    @property
    def max_image_size_bytes(self) -> int:
        return int(self.MAX_IMAGE_SIZE_MB * 1024 * 1024)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance (constructed once)."""
    return Settings()


# Module-level convenience alias so callers can do `from backend.core.config import settings`
settings: Settings = get_settings()
