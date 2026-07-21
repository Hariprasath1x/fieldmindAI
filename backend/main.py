from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from PIL import Image


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent


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

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "FieldMind backend is running."}


@app.post("/predict/disease")
async def predict_disease(file: UploadFile = File(...)) -> dict[str, Any]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload a JPG or PNG image.")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Could not read the uploaded image.") from exc

    disease_label, confidence, _ = run_classifier(image)

    if confidence < 0.60:
        return {
            "status": "unknown",
            "message": "This doesn't look like a recognized plant/leaf image. Please upload a clear photo of a plant leaf.",
        }

    severity_detections = run_yolo(image)
    return {
        "status": "ok",
        "disease": disease_label,
        "confidence": confidence,
        "severity_detections": severity_detections,
    }


@app.post("/predict/crop")
def predict_crop(payload: CropRequest) -> dict[str, str]:
    features = np.array([[payload.N, payload.P, payload.K, payload.temperature, payload.humidity, payload.ph, payload.rainfall]], dtype=np.float32)
    prediction = crop_model.predict(features)[0]

    if hasattr(crop_model, "classes_"):
        classes = list(crop_model.classes_)
        if isinstance(prediction, (np.integer, int)) and 0 <= int(prediction) < len(classes):
            prediction = classes[int(prediction)]

    return {"recommended_crop": str(prediction)}
