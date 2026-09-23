"""Centralised ML inference service for FieldMind.

All ONNX sessions are initialised **once** when this module is first imported
(or when ``MLInferenceService.initialise()`` is explicitly called).  Subsequent
calls reuse the loaded sessions, which avoids the significant per-request
overhead of loading large ONNX graphs repeatedly.

Usage
-----
    from backend.services.ml_inference import inference_service

    label, confidence, probs = inference_service.run_classifier(pil_image)
    detections          = inference_service.run_yolo(pil_image)
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import onnxruntime as ort
from PIL import Image

from backend.core.config import settings

logger = logging.getLogger("fieldmind.ml")

# ── Label helpers ────────────────────────────────────────────────────────────


def _load_indexed_labels(path: Path) -> list[str]:
    """Load labels from a JSON list or an index-keyed JSON object."""
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, list):
        return [str(item) for item in data]

    if isinstance(data, dict):
        try:
            return [
                str(data[key])
                for key in sorted(data.keys(), key=lambda v: int(v))
            ]
        except (TypeError, ValueError):
            return [str(data[key]) for key in sorted(data.keys())]

    raise ValueError(f"Unsupported label format in {path}")


def _resolve_model(filename: str, models_dir: Path) -> Path:
    """Find a model file; search backend/models then project models/."""
    backend_models = Path(__file__).resolve().parent.parent / "models" / filename
    project_models = models_dir / filename

    for candidate in (backend_models, project_models):
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        f"Could not find '{filename}' in backend/models or {models_dir}."
    )


# ── Preprocessing helpers ────────────────────────────────────────────────────


def _softmax(logits: np.ndarray) -> np.ndarray:
    arr = np.asarray(logits, dtype=np.float32)
    arr = arr - np.max(arr)
    exp = np.exp(arr)
    return exp / np.sum(exp)


def _preprocess_classifier(image: Image.Image) -> np.ndarray:
    """Standard ImageNet-normalised NCHW tensor for the disease classifier."""
    img = image.convert("RGB").resize((224, 224))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    arr = (arr - mean) / std
    arr = np.transpose(arr, (2, 0, 1))
    return np.expand_dims(arr, axis=0).astype(np.float32)


def _letterbox(
    image: Image.Image, target_hw: tuple[int, int]
) -> tuple[np.ndarray, float, tuple[float, float]]:
    """Resize with grey padding to preserve aspect ratio for YOLO."""
    img = image.convert("RGB")
    ow, oh = img.size
    th, tw = target_hw
    scale = min(tw / ow, th / oh)
    rw, rh = int(round(ow * scale)), int(round(oh * scale))
    resized = img.resize((rw, rh))
    canvas = Image.new("RGB", (tw, th), (114, 114, 114))
    pad_l = int((tw - rw) / 2)
    pad_t = int((th - rh) / 2)
    canvas.paste(resized, (pad_l, pad_t))
    arr = np.asarray(canvas, dtype=np.float32) / 255.0
    arr = np.transpose(arr, (2, 0, 1))
    return np.expand_dims(arr, axis=0).astype(np.float32), scale, (pad_l, pad_t)


def _clip_box(box: np.ndarray, w: int, h: int) -> list[float]:
    x1, y1, x2, y2 = box.tolist()
    return [
        float(max(0.0, min(x1, w))),
        float(max(0.0, min(y1, h))),
        float(max(0.0, min(x2, w))),
        float(max(0.0, min(y2, h))),
    ]


def _box_iou(a: np.ndarray, b: np.ndarray) -> float:
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - inter
    return float(inter / union) if union > 0 else 0.0


def _nms(
    detections: list[dict[str, Any]], iou_threshold: float
) -> list[dict[str, Any]]:
    if not detections:
        return []
    detections = sorted(detections, key=lambda d: d["confidence"], reverse=True)
    selected: list[dict[str, Any]] = []
    while detections:
        best = detections.pop(0)
        selected.append(best)
        remaining = []
        for cand in detections:
            if (
                cand["label"] != best["label"]
                or _box_iou(np.array(best["box"]), np.array(cand["box"]))
                < iou_threshold
            ):
                remaining.append(cand)
        detections = remaining
    return selected


# ── Main service class ────────────────────────────────────────────────────────


class MLInferenceService:
    """Holds loaded ONNX sessions and exposes typed inference methods.

    The service is safe to call from multiple coroutines/threads once
    initialised because ONNX Runtime sessions are thread-safe for read
    operations.
    """

    def __init__(self) -> None:
        self._classifier_session: ort.InferenceSession | None = None
        self._yolo_session: ort.InferenceSession | None = None
        self._crop_model: Any = None
        self._class_names: list[str] = []
        self._yolo_class_names: list[str] = []
        self._initialised = False
        self._init_error: str | None = None

        # Model metadata for the dashboard / evaluation endpoints
        self.classifier_model_name: str = "unknown"
        self.classifier_model_version: str = "1.0.0"

    # ── Initialisation ────────────────────────────────────────────────────

    def initialise(self, models_dir: Path | None = None) -> None:
        """Load all ML models.  Should be called once at application startup."""
        dir_ = models_dir or settings.MODELS_DIR
        if not dir_.is_absolute():
            # Resolve relative to project root (parent of backend/)
            dir_ = Path(__file__).resolve().parent.parent.parent / dir_

        start = time.perf_counter()
        try:
            self._load_classifier(dir_)
            self._load_yolo(dir_)
            self._load_crop_model(dir_)
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "ML models loaded",
                extra={
                    "models_dir": str(dir_),
                    "elapsed_ms": round(elapsed, 1),
                    "classifier": self.classifier_model_name,
                    "class_count": len(self._class_names),
                    "yolo_class_count": len(self._yolo_class_names),
                },
            )
            self._initialised = True
            self._init_error = None
        except Exception as exc:  # noqa: BLE001
            self._init_error = str(exc)
            logger.error("ML model loading failed", extra={"error": str(exc)})
            raise

    def _load_classifier(self, dir_: Path) -> None:
        for name in ("fieldmind_best.onnx", "fieldmind_pest.onnx"):
            try:
                path = _resolve_model(name, dir_)
                self._classifier_session = ort.InferenceSession(
                    str(path), providers=["CPUExecutionProvider"]
                )
                self.classifier_model_name = name
                break
            except FileNotFoundError:
                continue

        if self._classifier_session is None:
            raise FileNotFoundError(
                "No disease classifier ONNX model found in models directory."
            )

        names_path = _resolve_model("class_names.json", dir_)
        self._class_names = _load_indexed_labels(names_path)

    def _load_yolo(self, dir_: Path) -> None:
        path = _resolve_model("fieldmind_yolo_best.onnx", dir_)
        self._yolo_session = ort.InferenceSession(
            str(path), providers=["CPUExecutionProvider"]
        )
        yolo_path = _resolve_model("yolo_classes.json", dir_)
        self._yolo_class_names = _load_indexed_labels(yolo_path)

    def _load_crop_model(self, dir_: Path) -> None:
        path = _resolve_model("crop_model.pkl", dir_)
        self._crop_model = joblib.load(path)

    # ── Health helpers ────────────────────────────────────────────────────

    @property
    def is_ready(self) -> bool:
        return self._initialised and self._init_error is None

    @property
    def init_error(self) -> str | None:
        return self._init_error

    @property
    def class_names(self) -> list[str]:
        return list(self._class_names)

    @property
    def yolo_class_names(self) -> list[str]:
        return list(self._yolo_class_names)

    @property
    def crop_model(self) -> Any:
        return self._crop_model

    # ── Inference methods ─────────────────────────────────────────────────

    def run_classifier(
        self, image: Image.Image
    ) -> tuple[str, float, np.ndarray]:
        """Run the disease classifier.

        Returns:
            (label, confidence, full_probability_vector)
        """
        if self._classifier_session is None:
            raise RuntimeError("Disease classifier is not loaded.")

        t0 = time.perf_counter()
        input_name = self._classifier_session.get_inputs()[0].name
        tensor = _preprocess_classifier(image)
        raw = self._classifier_session.run(None, {input_name: tensor})[0]
        probs = _softmax(np.asarray(raw).squeeze())
        top_idx = int(np.argmax(probs))
        confidence = float(probs[top_idx])
        label = (
            self._class_names[top_idx]
            if top_idx < len(self._class_names)
            else str(top_idx)
        )
        elapsed = (time.perf_counter() - t0) * 1000
        logger.debug(
            "Classifier inference",
            extra={
                "label": label,
                "confidence": round(confidence, 4),
                "latency_ms": round(elapsed, 1),
            },
        )
        return label, confidence, probs

    def get_top_k_predictions(
        self, probs: np.ndarray, k: int = 3
    ) -> list[dict[str, Any]]:
        """Return the top-k predictions from a probability vector."""
        top_indices = np.argsort(probs)[::-1][:k]
        results = []
        for idx in top_indices:
            label = (
                self._class_names[int(idx)]
                if int(idx) < len(self._class_names)
                else str(idx)
            )
            results.append({"label": label, "confidence": float(probs[idx])})
        return results

    def run_yolo(self, image: Image.Image) -> list[dict[str, Any]]:
        """Run the YOLO severity/localisation model.

        Returns:
            List of detection dicts with keys: label, confidence, box.
        """
        if self._yolo_session is None:
            raise RuntimeError("YOLO model is not loaded.")

        t0 = time.perf_counter()
        shape = self._yolo_session.get_inputs()[0].shape
        ih = shape[2] if isinstance(shape[2], int) and shape[2] > 0 else 640
        iw = shape[3] if isinstance(shape[3], int) and shape[3] > 0 else 640
        input_name = self._yolo_session.get_inputs()[0].name
        tensor, scale, pad = _letterbox(image, (ih, iw))
        outputs = self._yolo_session.run(None, {input_name: tensor})

        detections = self._decode_yolo(outputs, image.size, scale, pad)
        elapsed = (time.perf_counter() - t0) * 1000
        logger.debug(
            "YOLO inference",
            extra={
                "detections": len(detections),
                "latency_ms": round(elapsed, 1),
            },
        )
        return detections

    def _decode_yolo(
        self,
        outputs: list[np.ndarray],
        original_size: tuple[int, int],
        scale: float,
        pad: tuple[float, float],
    ) -> list[dict[str, Any]]:
        raw = np.asarray(outputs[0])
        if raw.ndim == 3:
            raw = raw[0]
        n_classes = len(self._yolo_class_names)
        if raw.shape[0] == 4 + n_classes:
            raw = raw.transpose(1, 0)
        if raw.shape[-1] != 4 + n_classes:
            return []

        boxes = raw[:, :4].astype(np.float32)
        class_scores = raw[:, 4:].astype(np.float32)
        if class_scores.size == 0:
            return []

        class_ids = np.argmax(class_scores, axis=1)
        confidences = class_scores[np.arange(class_scores.shape[0]), class_ids]
        if np.max(class_scores) > 1.0:
            confidences = 1.0 / (1.0 + np.exp(-confidences))

        ow, oh = original_size
        pad_x, pad_y = pad
        detections: list[dict[str, Any]] = []

        for box, cid, conf in zip(boxes, class_ids, confidences):
            if float(conf) < settings.YOLO_CONFIDENCE_THRESHOLD:
                continue
            cx, cy, bw, bh = box.tolist()
            x1 = (cx - bw / 2 - pad_x) / scale
            y1 = (cy - bh / 2 - pad_y) / scale
            x2 = (cx + bw / 2 - pad_x) / scale
            y2 = (cy + bh / 2 - pad_y) / scale
            clipped = _clip_box(np.array([x1, y1, x2, y2]), ow, oh)
            lbl = (
                self._yolo_class_names[int(cid)]
                if int(cid) < len(self._yolo_class_names)
                else str(cid)
            )
            detections.append(
                {"label": lbl, "confidence": float(conf), "box": clipped}
            )

        return _nms(detections, settings.YOLO_IOU_THRESHOLD)

    def compute_affected_area_pct(
        self,
        detections: list[dict[str, Any]],
        image_size: tuple[int, int],
    ) -> float | None:
        """Estimate affected area as union of bounding boxes / image area.

        NOTE: This is a bounding-box approximation. It over-estimates the true
        affected leaf area since boxes enclose the region rather than segment it.
        Returns None when there are no detections.
        """
        if not detections:
            return None

        ow, oh = image_size
        image_area = ow * oh
        if image_area == 0:
            return None

        # Build union mask via simple accumulation
        union_area = 0.0
        # Approximate union using set coverage of individual boxes
        covered: set[tuple[int, int]] = set()
        for det in detections:
            box = det.get("box", [])
            if len(box) != 4:
                continue
            x1, y1, x2, y2 = [int(v) for v in box]
            for px in range(x1, min(x2, ow)):
                for py in range(y1, min(y2, oh)):
                    covered.add((px, py))
        union_area = len(covered)

        if union_area == 0:
            return None

        pct = (union_area / image_area) * 100.0
        return round(min(pct, 100.0), 2)


# ── Module-level singleton ────────────────────────────────────────────────────

inference_service = MLInferenceService()
