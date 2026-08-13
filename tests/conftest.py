"""Shared pytest fixtures for FieldMind tests."""
from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ── Image factories ───────────────────────────────────────────────────────────


def make_green_image(width: int = 300, height: int = 300) -> Image.Image:
    """Create a sharp, green leaf-like image for testing."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    # Green channel dominant
    arr[:, :, 1] = 150
    # Add some texture variation to avoid zero-variance blur detection
    arr[::5, ::5, 0] = 80
    arr[::5, ::5, 2] = 30
    return Image.fromarray(arr, "RGB")


def make_blurry_image(width: int = 300, height: int = 300) -> Image.Image:
    """Create a solid-colour image that will score low on Laplacian variance."""
    arr = np.full((height, width, 3), 128, dtype=np.uint8)
    return Image.fromarray(arr, "RGB")


def make_tiny_image(width: int = 30, height: int = 30) -> Image.Image:
    return make_green_image(width, height)


def image_to_bytes(image: Image.Image, fmt: str = "JPEG") -> bytes:
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    return buf.getvalue()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def green_image() -> Image.Image:
    return make_green_image()


@pytest.fixture
def green_image_bytes() -> bytes:
    return image_to_bytes(make_green_image())


@pytest.fixture
def blurry_image_bytes() -> bytes:
    return image_to_bytes(make_blurry_image())


@pytest.fixture
def tiny_image_bytes() -> bytes:
    return image_to_bytes(make_tiny_image())


@pytest.fixture
def mock_inference_service():
    """Mock MLInferenceService that returns predictable results without loading models."""
    svc = MagicMock()
    svc.is_ready = True
    svc.classifier_model_name = "fieldmind_pest.onnx"
    svc.classifier_model_version = "1.0.0"
    svc.class_names = [
        "cashew_anthracnose", "cashew_healthy",
        "tomato_leaf_blight", "tomato_healthy",
    ]
    probs = np.array([0.85, 0.05, 0.05, 0.05], dtype=np.float32)
    svc.run_classifier.return_value = ("cashew_anthracnose", 0.85, probs)
    svc.get_top_k_predictions.return_value = [
        {"label": "cashew_anthracnose", "confidence": 0.85},
        {"label": "cashew_healthy", "confidence": 0.05},
    ]
    svc.run_yolo.return_value = [
        {
            "label": "anthracnose",
            "confidence": 0.78,
            "box": [50.0, 60.0, 200.0, 180.0],
        }
    ]
    svc.compute_affected_area_pct.return_value = 12.5
    svc.crop_model = MagicMock()
    return svc


@pytest.fixture
def mock_leaf_verifier():
    """Mock LeafVerifier that approves all images as leaves."""
    lv = MagicMock()
    lv.predict.return_value = {
        "success": True,
        "verification": {
            "is_leaf": True,
            "status": "verified",
            "confidence": 0.97,
            "predicted_class": "leaf",
        },
        "pipeline": {"allow_processing": True, "next_step": "disease_detection"},
    }
    return lv


@pytest.fixture
def mock_leaf_verifier_reject():
    """Mock LeafVerifier that rejects all images."""
    lv = MagicMock()
    lv.predict.return_value = {
        "success": True,
        "verification": {
            "is_leaf": False,
            "status": "rejected",
            "confidence": 0.92,
            "predicted_class": "non_leaf",
        },
        "pipeline": {"allow_processing": False, "next_step": "upload_again"},
        "message": "Please upload a clear image of a single plant leaf.",
    }
    return lv


@pytest.fixture
def mock_firestore():
    """In-memory mock Firestore database."""
    from backend.db.firebase import MockFirestore
    return MockFirestore()


@pytest.fixture
def fastapi_client(mock_inference_service, mock_leaf_verifier):
    """Test client with mocked ML services."""
    from fastapi.testclient import TestClient
    from backend.main import app

    app.state.ml_service = mock_inference_service
    app.state.leaf_verifier = mock_leaf_verifier

    # Patch both the module singleton AND the worker's already-imported reference.
    # The worker does `from backend.services.ml_inference import inference_service`
    # at import time, creating a local binding that won't be updated by patching
    # the original module attribute alone.
    with patch("backend.services.ml_inference.inference_service", mock_inference_service), \
         patch("backend.worker.inference_worker.inference_service", mock_inference_service), \
         patch("backend.main.inference_service", mock_inference_service):
        with TestClient(app) as client:
            yield client
