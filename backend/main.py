"""FieldMind FastAPI application entry point.

This file wires together all routers and initialises shared state.
Business logic lives in routers/ and services/ — not here.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np

from backend.core.config import settings
from backend.core.logging_config import configure_logging
from backend.core.request_id import RequestIDMiddleware
from backend.services.leaf_verifier import (
    LeafVerifier,
    LeafVerifierInitializationError,
)
from backend.services.ml_inference import inference_service
from backend.routers.marketplace import router as marketplace_router
from backend.routers.diagnosis import router as diagnosis_router
from backend.routers.inference import router as inference_router
from backend.routers.feedback import router as feedback_router
from backend.routers.health import router as health_router
from backend.routers.ml_dashboard import router as ml_dashboard_router
from backend.services.recommendation_reason_service import get_crop_metadata, generate_reasons

# ── Logging ───────────────────────────────────────────────────────────────────

configure_logging(
    level=settings.LOG_LEVEL,
    json_format=settings.is_production,
)
logger = logging.getLogger("fieldmind")

# ── Application ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise all ML models once at startup."""
    # ── Leaf verifier ─────────────────────────────────────────────────
    try:
        app.state.leaf_verifier = LeafVerifier(
            model_path=_resolve_model_path("leaf_verifier.onnx"),
            config_path=_resolve_model_path("leaf_verifier_config.json"),
            labels_path=_resolve_model_path("labels.json"),
        )
        logger.info("Leaf verifier initialised.")
    except (FileNotFoundError, LeafVerifierInitializationError) as exc:
        app.state.leaf_verifier_error = str(exc)
        logger.error("Leaf verifier init failed: %s", exc)

    # ── Disease classifier + YOLO + crop model ────────────────────────
    models_dir = Path(__file__).resolve().parent.parent / settings.MODELS_DIR
    try:
        inference_service.initialise(models_dir)
        app.state.ml_service = inference_service
        logger.info("ML inference service initialised.")
    except Exception as exc:
        logger.error("ML service init failed: %s", exc)
        
    yield


app = FastAPI(
    title="FieldMind API",
    version="2.0.0",
    description=(
        "Production-ready agricultural AI/ML API. "
        "Provides disease detection, crop recommendation, and marketplace services."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.leaf_verifier = None
app.state.leaf_verifier_error = None
app.state.ml_service = None

# ── Middleware ────────────────────────────────────────────────────────────────

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(health_router)
app.include_router(marketplace_router)
app.include_router(diagnosis_router)
app.include_router(inference_router)
app.include_router(feedback_router)
app.include_router(ml_dashboard_router)


# ── Startup ───────────────────────────────────────────────────────────────────

def _resolve_model_path(filename: str) -> Path:
    base = Path(__file__).resolve().parent
    project = base.parent

    candidates = [
        base / "models" / filename,
        project / settings.MODELS_DIR / filename,
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"Could not find '{filename}' in models directories.")




# ── Root endpoint ─────────────────────────────────────────────────────────────


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "FieldMind API v2.0.0 is running.",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
    }


# ── Legacy /predict/disease endpoint (kept for backwards compatibility) ────────
# The new async pipeline is at POST /api/inference/submit
# This endpoint remains synchronous for backward compatibility.


@app.post("/predict/disease", tags=["Disease Detection (Legacy)"])
async def predict_disease_legacy(file: UploadFile = File(...)) -> dict[str, Any]:
    """Legacy synchronous disease detection endpoint.

    Prefer POST /api/inference/submit for the full validated async pipeline.
    """
    from backend.worker.inference_worker import run_inference_job
    import uuid

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    job_id = str(uuid.uuid4())
    from backend.db.firebase import get_db
    from datetime import datetime, timezone
    db = get_db()
    now = datetime.now(tz=timezone.utc).isoformat()
    db.collection("inference_jobs").document(job_id).set(
        {
            "job_id": job_id,
            "status": "queued",
            "user_id": None,
            "plant_id": None,
            "field_id": None,
            "request_id": "legacy",
            "created_at": now,
            "updated_at": now,
            "result": None,
            "error": None,
        }
    )

    result = run_inference_job(
        job_id=job_id,
        image_bytes=image_bytes,
        content_type=file.content_type,
        filename=file.filename,
        user_id=None,
        plant_id=None,
        field_id=None,
        leaf_verifier=app.state.leaf_verifier,
    )

    return result


# ── Crop recommendation (kept from original) ──────────────────────────────────


class CropRequest(BaseModel):
    N: float = Field(..., description="Soil nitrogen")
    P: float = Field(..., description="Soil phosphorus")
    K: float = Field(..., description="Soil potassium")
    temperature: float
    humidity: float
    ph: float = Field(..., alias="pH")
    rainfall: float


@app.post("/predict/crop", tags=["Crop Recommendation"])
def predict_crop(payload: CropRequest) -> dict[str, Any]:
    """Crop recommendation using the trained scikit-learn model."""
    if not inference_service.is_ready or inference_service.crop_model is None:
        raise HTTPException(
            status_code=503,
            detail="Crop recommendation model is not available.",
        )

    crop_model = inference_service.crop_model
    features = np.array(
        [[payload.N, payload.P, payload.K, payload.temperature, payload.humidity, payload.ph, payload.rainfall]],
        dtype=np.float32,
    )

    if hasattr(crop_model, "predict_proba"):
        probabilities = crop_model.predict_proba(features)[0]
        classes = list(crop_model.classes_)
        top_indices = np.argsort(probabilities)[-3:][::-1]

        recommendations = []
        for i, idx in enumerate(top_indices):
            crop_name = str(classes[idx])
            confidence = round(float(probabilities[idx]) * 100, 2)
            metadata = get_crop_metadata(crop_name)
            is_top = i == 0
            reasons = generate_reasons(crop_name, payload, is_top)
            recommendations.append(
                {
                    "crop": crop_name,
                    "confidence": confidence,
                    "season": metadata["season"],
                    "water_requirement": metadata["water_requirement"],
                    "water_range": metadata["water_range"],
                    "difficulty": metadata["difficulty"],
                    "description": metadata["description"],
                    "reasons": reasons,
                }
            )
        return {"recommendations": recommendations}

    prediction = crop_model.predict(features)[0]
    if hasattr(crop_model, "classes_"):
        classes = list(crop_model.classes_)
        if isinstance(prediction, (np.integer, int)) and 0 <= int(prediction) < len(classes):
            prediction = classes[int(prediction)]

    crop_name = str(prediction)
    metadata = get_crop_metadata(crop_name)
    reasons = generate_reasons(crop_name, payload, True)
    return {
        "recommendations": [
            {
                "crop": crop_name,
                "confidence": 100.0,
                "season": metadata["season"],
                "water_requirement": metadata["water_requirement"],
                "water_range": metadata["water_range"],
                "difficulty": metadata["difficulty"],
                "description": metadata["description"],
                "reasons": reasons,
            }
        ]
    }


# ── Location endpoint (kept from original) ────────────────────────────────────


class LocationRequest(BaseModel):
    latitude: float
    longitude: float


LOCATION_CACHE: dict[str, Any] = {}


@app.post("/api/location/collect", tags=["Location"])
async def collect_location_data(payload: LocationRequest) -> dict[str, Any]:
    from backend.services.location_service import get_location_info
    from backend.services.weather_service import get_weather_info
    from backend.services.soil_service import get_soil_info
    from backend.services.estimation_service import estimate_npk

    lat = round(payload.latitude, 4)
    lon = round(payload.longitude, 4)
    cache_key = f"{lat},{lon}"

    if cache_key in LOCATION_CACHE:
        logger.debug("Location cache hit for %s", cache_key)
        return LOCATION_CACHE[cache_key]

    location_data = get_location_info(lat, lon)
    weather_data = get_weather_info(lat, lon)
    soil_data = get_soil_info(lat, lon)
    estimated_npk = estimate_npk(soil_data, weather_data)

    response_data = {
        "location": location_data,
        "weather": weather_data,
        "soil": soil_data,
        "estimated": estimated_npk,
    }
    LOCATION_CACHE[cache_key] = response_data
    return response_data
