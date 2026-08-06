from __future__ import annotations

import io
import json
import logging
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image

from backend.services.leaf_verifier import LeafVerifier, LeafVerifierInferenceError, LeafVerifierInitializationError
from backend.services.location_service import get_location_info
from backend.services.soil_service import get_soil_info
from backend.services.estimation_service import estimate_npk
from backend.services.recommendation_reason_service import get_crop_metadata, generate_reasons
from backend.routers.marketplace import router as marketplace_router

class LocationRequest(BaseModel):
    latitude: float
    longitude: float

LOCATION_CACHE = {}

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
logger = logging.getLogger("fieldmind")


def resolve_model_path(filename: str) -> Path:
    """Look for models in backend/models first, then the workspace models folder."""

    candidates = [BASE_DIR / "models" / filename, PROJECT_DIR / "models" / filename]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find {filename} in backend/models or models/")


def load_indexed_labels(path: Path) -> list[str]:
    """Load labels from a JSON list or an index-keyed JSON object."""

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if isinstance(data, list):
        return [str(item) for item in data]

    if isinstance(data, dict):
        try:
            return [str(data[key]) for key in sorted(data.keys(), key=lambda value: int(value))]
        except (TypeError, ValueError):
            return [str(data[key]) for key in sorted(data.keys())]

    raise ValueError(f"Unsupported label format in {path}")


CLASSIFIER_MODEL_PATH = None
for candidate_name in ["fieldmind_best.onnx", "fieldmind_pest.onnx"]:
    try:
        CLASSIFIER_MODEL_PATH = resolve_model_path(candidate_name)
        break
    except FileNotFoundError:
        continue

if CLASSIFIER_MODEL_PATH is None:
    raise FileNotFoundError("Could not find an ONNX classifier model in the models folders.")

YOLO_MODEL_PATH = resolve_model_path("fieldmind_yolo_best.onnx")
CROP_MODEL_PATH = resolve_model_path("crop_model.pkl")
CLASS_NAMES_PATH = resolve_model_path("class_names.json")
YOLO_CLASSES_PATH = resolve_model_path("yolo_classes.json")


class_names = load_indexed_labels(CLASS_NAMES_PATH)
yolo_class_names = load_indexed_labels(YOLO_CLASSES_PATH)

classifier_session = ort.InferenceSession(str(CLASSIFIER_MODEL_PATH), providers=["CPUExecutionProvider"])
yolo_session = ort.InferenceSession(str(YOLO_MODEL_PATH), providers=["CPUExecutionProvider"])
crop_model = joblib.load(CROP_MODEL_PATH)


def get_input_hw(session: ort.InferenceSession, default: tuple[int, int]) -> tuple[int, int]:
    shape = session.get_inputs()[0].shape
    height, width = default

    if len(shape) >= 4:
        raw_height = shape[2]
        raw_width = shape[3]
        if isinstance(raw_height, int) and raw_height > 0:
            height = raw_height
        if isinstance(raw_width, int) and raw_width > 0:
            width = raw_width

    return height, width


def softmax(logits: np.ndarray) -> np.ndarray:
    logits = np.asarray(logits, dtype=np.float32)
    logits = logits - np.max(logits)
    exponentiated = np.exp(logits)
    return exponentiated / np.sum(exponentiated)


def preprocess_classifier_image(image: Image.Image) -> np.ndarray:
    """Resize, normalize, and convert the image into NCHW float32 format."""

    target_size = (224, 224)
    image = image.convert("RGB").resize(target_size)
    array = np.asarray(image, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    array = (array - mean) / std
    array = np.transpose(array, (2, 0, 1))
    return np.expand_dims(array, axis=0).astype(np.float32)


def letterbox_image(image: Image.Image, new_shape: tuple[int, int]) -> tuple[np.ndarray, float, tuple[float, float]]:
    """Resize with padding so the YOLO input keeps the original aspect ratio."""

    image = image.convert("RGB")
    original_width, original_height = image.size
    target_height, target_width = new_shape
    scale = min(target_width / original_width, target_height / original_height)
    resized_width = int(round(original_width * scale))
    resized_height = int(round(original_height * scale))

    resized = image.resize((resized_width, resized_height))
    canvas = Image.new("RGB", (target_width, target_height), (114, 114, 114))
    pad_left = int((target_width - resized_width) / 2)
    pad_top = int((target_height - resized_height) / 2)
    canvas.paste(resized, (pad_left, pad_top))

    array = np.asarray(canvas, dtype=np.float32) / 255.0
    array = np.transpose(array, (2, 0, 1))
    return np.expand_dims(array, axis=0).astype(np.float32), scale, (pad_left, pad_top)


def clip_box(box: np.ndarray, width: int, height: int) -> list[float]:
    x1, y1, x2, y2 = box.tolist()
    x1 = float(max(0.0, min(x1, width)))
    y1 = float(max(0.0, min(y1, height)))
    x2 = float(max(0.0, min(x2, width)))
    y2 = float(max(0.0, min(y2, height)))
    return [x1, y1, x2, y2]


def box_iou(box_a: np.ndarray, box_b: np.ndarray) -> float:
    x1 = max(box_a[0], box_b[0])
    y1 = max(box_a[1], box_b[1])
    x2 = min(box_a[2], box_b[2])
    y2 = min(box_a[3], box_b[3])

    inter_width = max(0.0, x2 - x1)
    inter_height = max(0.0, y2 - y1)
    intersection = inter_width * inter_height

    area_a = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
    area_b = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
    union = area_a + area_b - intersection
    if union <= 0.0:
        return 0.0
    return float(intersection / union)


def non_max_suppression(detections: list[dict[str, Any]], iou_threshold: float = 0.45) -> list[dict[str, Any]]:
    if not detections:
        return []

    detections = sorted(detections, key=lambda item: item["confidence"], reverse=True)
    selected: list[dict[str, Any]] = []

    while detections:
        best = detections.pop(0)
        selected.append(best)
        remaining: list[dict[str, Any]] = []
        for candidate in detections:
            if candidate["label"] != best["label"] or box_iou(np.array(best["box"]), np.array(candidate["box"])) < iou_threshold:
                remaining.append(candidate)
        detections = remaining

    return selected


def run_classifier(image: Image.Image) -> tuple[str, float, np.ndarray]:
    input_name = classifier_session.get_inputs()[0].name
    input_tensor = preprocess_classifier_image(image)
    raw_output = classifier_session.run(None, {input_name: input_tensor})[0]
    logits = np.asarray(raw_output).squeeze()
    probabilities = softmax(logits)
    top_index = int(np.argmax(probabilities))
    confidence = float(probabilities[top_index])
    label = class_names[top_index] if top_index < len(class_names) else str(top_index)
    return label, confidence, probabilities


def decode_yolo_output(outputs: list[np.ndarray], original_size: tuple[int, int], input_size: tuple[int, int], scale: float, pad: tuple[float, float]) -> list[dict[str, Any]]:
    raw_output = np.asarray(outputs[0])
    if raw_output.ndim == 3:
        raw_output = raw_output[0]

    if raw_output.shape[0] == 4 + len(yolo_class_names):
        raw_output = raw_output.transpose(1, 0)

    if raw_output.shape[-1] != 4 + len(yolo_class_names):
        return []

    boxes = raw_output[:, :4].astype(np.float32)
    class_scores = raw_output[:, 4:].astype(np.float32)

    if class_scores.size == 0:
        return []

    class_ids = np.argmax(class_scores, axis=1)
    confidences = class_scores[np.arange(class_scores.shape[0]), class_ids]

    if np.max(class_scores) > 1.0:
        confidences = 1.0 / (1.0 + np.exp(-confidences))

    detections: list[dict[str, Any]] = []
    original_width, original_height = original_size
    pad_x, pad_y = pad

    for box, class_id, confidence in zip(boxes, class_ids, confidences):
        if float(confidence) < 0.25:
            continue

        x_center, y_center, width, height = box.tolist()
        x1 = (x_center - width / 2 - pad_x) / scale
        y1 = (y_center - height / 2 - pad_y) / scale
        x2 = (x_center + width / 2 - pad_x) / scale
        y2 = (y_center + height / 2 - pad_y) / scale
        clipped_box = clip_box(np.array([x1, y1, x2, y2]), original_width, original_height)

        label_index = int(class_id)
        label = yolo_class_names[label_index] if label_index < len(yolo_class_names) else str(label_index)
        detections.append({"label": label, "confidence": float(confidence), "box": clipped_box})

    return non_max_suppression(detections)


def run_yolo(image: Image.Image) -> list[dict[str, Any]]:
    input_height, input_width = get_input_hw(yolo_session, (640, 640))
    input_name = yolo_session.get_inputs()[0].name
    input_tensor, scale, pad = letterbox_image(image, (input_height, input_width))
    outputs = yolo_session.run(None, {input_name: input_tensor})
    return decode_yolo_output(outputs, image.size, (input_height, input_width), scale, pad)


class CropRequest(BaseModel):
    N: float = Field(..., description="Soil nitrogen")
    P: float = Field(..., description="Soil phosphorus")
    K: float = Field(..., description="Soil potassium")
    temperature: float
    humidity: float
    ph: float = Field(..., alias="pH")
    rainfall: float


app = FastAPI(title="FieldMind API", version="1.0.0")
app.state.leaf_verifier = None
app.state.leaf_verifier_error = None

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(marketplace_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "FieldMind backend is running."}


@app.on_event("startup")
def startup_leaf_verifier() -> None:
    """Initialize the leaf verifier once during application startup."""

    try:
        app.state.leaf_verifier = LeafVerifier(
            model_path=resolve_model_path("leaf_verifier.onnx"),
            config_path=resolve_model_path("leaf_verifier_config.json"),
            labels_path=resolve_model_path("labels.json"),
        )
        app.state.leaf_verifier_error = None
        logger.info("Leaf verifier initialized successfully.")
    except (FileNotFoundError, LeafVerifierInitializationError) as exc:
        app.state.leaf_verifier = None
        app.state.leaf_verifier_error = str(exc)
        logger.error("Leaf verifier initialization failed: %s", exc)


def get_leaf_verifier() -> LeafVerifier:
    verifier = getattr(app.state, "leaf_verifier", None)
    if verifier is not None:
        return verifier

    raise HTTPException(status_code=503, detail="Leaf verification is temporarily unavailable.")


def load_uploaded_image(image_bytes: bytes) -> Image.Image:
    """Load and fully decode an uploaded image."""

    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
        return image
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Could not read the uploaded image.") from exc


def build_recommendation(disease_label: str, disease_confidence: float, severity_detections: list[dict[str, Any]]) -> str:
    if disease_confidence < 0.60:
        return "This image was too uncertain for disease analysis. Please upload a clearer plant leaf image."

    if not severity_detections:
        return f"Detected {disease_label}. No severity boxes were returned, so continue monitoring the plant closely."

    top_detection = max(severity_detections, key=lambda item: float(item.get("confidence", 0.0)))
    label = top_detection.get("label", "the affected area")
    return f"Detected {disease_label}. Review {label} and apply the appropriate treatment based on local agronomy guidance."


def build_bounding_boxes(severity_detections: list[dict[str, Any]]) -> list[list[float]]:
    return [list(map(float, detection.get("box", []))) for detection in severity_detections if detection.get("box")]


@app.post("/predict/disease")
async def predict_disease(file: UploadFile = File(...)) -> dict[str, Any]:
    request_started_at = time.perf_counter()

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a JPG or PNG image.")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Could not read the uploaded image.")

    image = load_uploaded_image(image_bytes)
    verifier = get_leaf_verifier()

    try:
        verification_result = verifier.predict(image)
    except LeafVerifierInferenceError as exc:
        logger.error("Leaf verification inference failed: %s", exc)
        raise HTTPException(status_code=502, detail="Leaf verification failed.") from exc
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected leaf verification failure: %s", exc)
        raise HTTPException(status_code=500, detail="Unexpected error during leaf verification.") from exc

    verification = verification_result["verification"]
    pipeline = verification_result["pipeline"]
    logger.info(
        "Leaf verification result=%s confidence=%.4f",
        verification["status"],
        float(verification["confidence"]),
    )

    if not pipeline["allow_processing"]:
        total_request_ms = (time.perf_counter() - request_started_at) * 1000.0
        logger.info("Total request time=%.2f ms", total_request_ms)
        return verification_result

    disease_started_at = time.perf_counter()
    try:
        disease_label, disease_confidence, _ = run_classifier(image)
    except ort.OrtError as exc:
        logger.error("Disease classification failed: %s", exc)
        raise HTTPException(status_code=502, detail="Disease classification failed.") from exc
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected disease classification failure: %s", exc)
        raise HTTPException(status_code=500, detail="Unexpected error during disease classification.") from exc

    logger.info("Disease prediction=%s confidence=%.4f", disease_label, disease_confidence)

    severity_detections: list[dict[str, Any]] = []
    yolo_execution_ms = 0.0
    if disease_confidence >= 0.60:
        try:
            severity_started_at = time.perf_counter()
            severity_detections = run_yolo(image)
            yolo_execution_ms = (time.perf_counter() - severity_started_at) * 1000.0
        except ort.OrtError as exc:
            logger.error("YOLO inference failed: %s", exc)
            raise HTTPException(status_code=502, detail="Severity detection failed.") from exc
        except Exception as exc:  # noqa: BLE001
            logger.error("Unexpected YOLO failure: %s", exc)
            raise HTTPException(status_code=500, detail="Unexpected error during severity detection.") from exc

        logger.info("YOLO execution time=%.2f ms", yolo_execution_ms)
    else:
        logger.info("YOLO execution skipped because disease confidence was below threshold.")

    total_request_ms = (time.perf_counter() - request_started_at) * 1000.0
    bounding_boxes = build_bounding_boxes(severity_detections)
    recommendation = build_recommendation(disease_label, disease_confidence, severity_detections)

    response: dict[str, Any] = {
        "success": True,
        "verification": verification,
        "pipeline": pipeline,
        "status": "ok" if disease_confidence >= 0.60 else "unknown",
        "disease": disease_label,
        "confidence": disease_confidence,
        "disease_prediction": {
            "label": disease_label,
            "confidence": disease_confidence,
        },
        "severity": {
            "detections": severity_detections,
            "bounding_boxes": bounding_boxes,
        },
        "severity_detections": severity_detections,
        "bounding_boxes": bounding_boxes,
        "recommendation": recommendation,
    }

    if disease_confidence < 0.60:
        response["message"] = "This doesn't look like a recognized plant/leaf image. Please upload a clear photo of a plant leaf."

    logger.info("Total request time=%.2f ms", total_request_ms)
    return response


@app.post("/predict/crop")
def predict_crop(payload: CropRequest) -> dict[str, Any]:
    features = np.array([[payload.N, payload.P, payload.K, payload.temperature, payload.humidity, payload.ph, payload.rainfall]], dtype=np.float32)
    
    if hasattr(crop_model, "predict_proba"):
        probabilities = crop_model.predict_proba(features)[0]
        classes = list(crop_model.classes_)
        
        # Get top 3 indices
        top_indices = np.argsort(probabilities)[-3:][::-1]
        
        recommendations = []
        for i, idx in enumerate(top_indices):
            crop_name = str(classes[idx])
            confidence = round(float(probabilities[idx]) * 100, 2)
            
            metadata = get_crop_metadata(crop_name)
            is_top = (i == 0)
            reasons = generate_reasons(crop_name, payload, is_top)
            
            recommendations.append({
                "crop": crop_name,
                "confidence": confidence,
                "season": metadata["season"],
                "water_requirement": metadata["water_requirement"],
                "water_range": metadata["water_range"],
                "difficulty": metadata["difficulty"],
                "description": metadata["description"],
                "reasons": reasons
            })
            
        return {"recommendations": recommendations}
    else:
        # Fallback if model doesn't support predict_proba
        prediction = crop_model.predict(features)[0]
        if hasattr(crop_model, "classes_"):
            classes = list(crop_model.classes_)
            if isinstance(prediction, (np.integer, int)) and 0 <= int(prediction) < len(classes):
                prediction = classes[int(prediction)]
                
        crop_name = str(prediction)
        metadata = get_crop_metadata(crop_name)
        reasons = generate_reasons(crop_name, payload, True)
        
        return {"recommendations": [{
            "crop": crop_name,
            "confidence": 100.0,
            "season": metadata["season"],
            "water_requirement": metadata["water_requirement"],
            "water_range": metadata["water_range"],
            "difficulty": metadata["difficulty"],
            "description": metadata["description"],
            "reasons": reasons
        }]}


@app.post("/api/location/collect")
async def collect_location_data(payload: LocationRequest) -> dict[str, Any]:
    lat = round(payload.latitude, 4)
    lon = round(payload.longitude, 4)
    cache_key = f"{lat},{lon}"
    
    if cache_key in LOCATION_CACHE:
        logger.info(f"Returning cached location data for {cache_key}")
        return LOCATION_CACHE[cache_key]
        
    logger.info(f"Fetching location data for {cache_key}")
    
    location_data = get_location_info(lat, lon)
    weather_data = get_weather_info(lat, lon)
    soil_data = get_soil_info(lat, lon)
    estimated_npk = estimate_npk(soil_data, weather_data)
    
    response_data = {
        "location": location_data,
        "weather": weather_data,
        "soil": soil_data,
        "estimated": estimated_npk
    }
    
    # Cache the result
    LOCATION_CACHE[cache_key] = response_data
    return response_data
