from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
from PIL import Image


class LeafVerifierInitializationError(RuntimeError):
    """Raised when the leaf verifier cannot be created."""


class LeafVerifierInferenceError(RuntimeError):
    """Raised when leaf verification inference fails."""


def softmax(logits: np.ndarray) -> np.ndarray:
    """Return numerically stable softmax probabilities."""

    logits = np.asarray(logits, dtype=np.float32).reshape(-1)
    logits = logits - np.max(logits)
    exponentiated = np.exp(logits)
    return exponentiated / np.sum(exponentiated)


class LeafVerifier:
    """Reusable ONNX-based leaf verification service."""

    def __init__(self, model_path: Path, config_path: Path, labels_path: Path) -> None:
        self.model_path = model_path
        self.config_path = config_path
        self.labels_path = labels_path

        self.config = self._load_json(config_path)
        self.labels = self._load_labels(labels_path)
        self.input_size = self._load_input_size(self.config)
        self.mean, self.std = self._load_normalization(self.config)
        self.confidence_threshold = float(self.config.get("confidence_threshold", 0.85))
        self.color_mode = str(self.config.get("preprocessing", {}).get("color", "RGB")).upper()
        self.session = self._create_session(model_path)
        self.input_name = self.session.get_inputs()[0].name

        self.non_leaf_label = self._select_label("non_leaf")
        self.leaf_label = self._select_label("leaf")

    @staticmethod
    def _load_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise LeafVerifierInitializationError(f"Missing required file: {path.name}")

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise LeafVerifierInitializationError(f"Invalid JSON structure in {path.name}")

        return data

    @staticmethod
    def _load_labels(path: Path) -> list[str]:
        if not path.exists():
            raise LeafVerifierInitializationError(f"Missing required file: {path.name}")

        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, list):
            labels = [str(item) for item in data]
        elif isinstance(data, dict):
            try:
                labels = [str(data[key]) for key in sorted(data.keys(), key=lambda value: int(value))]
            except (TypeError, ValueError):
                labels = [str(data[key]) for key in sorted(data.keys())]
        else:
            raise LeafVerifierInitializationError(f"Unsupported label format in {path.name}")

        if not labels:
            raise LeafVerifierInitializationError(f"No labels found in {path.name}")

        return labels

    @staticmethod
    def _load_input_size(config: dict[str, Any]) -> tuple[int, int]:
        input_config = config.get("input", {})
        width = int(input_config.get("width", 224))
        height = int(input_config.get("height", 224))

        if width <= 0 or height <= 0:
            raise LeafVerifierInitializationError("Leaf verifier input size must be positive.")

        return height, width

    @staticmethod
    def _load_normalization(config: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
        preprocessing = config.get("preprocessing", {})
        normalization = preprocessing.get("normalize", {})

        try:
            mean = np.asarray(normalization["mean"], dtype=np.float32)
            std = np.asarray(normalization["std"], dtype=np.float32)
        except KeyError as exc:
            raise LeafVerifierInitializationError("Leaf verifier normalization values are missing.") from exc

        if mean.shape != (3,) or std.shape != (3,):
            raise LeafVerifierInitializationError("Leaf verifier normalization values must contain 3 channels.")

        if np.any(std == 0):
            raise LeafVerifierInitializationError("Leaf verifier std values must be non-zero.")

        return mean, std

    @staticmethod
    def _create_session(model_path: Path) -> ort.InferenceSession:
        if not model_path.exists():
            raise LeafVerifierInitializationError(f"Missing required file: {model_path.name}")

        try:
            return ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        except ort.OrtError as exc:
            raise LeafVerifierInitializationError("Failed to initialize the leaf verifier model.") from exc

    def _select_label(self, expected_name: str) -> str:
        expected_name = expected_name.lower()
        normalized_labels = [label.lower() for label in self.labels]

        for index, label in enumerate(normalized_labels):
            if label == expected_name:
                return self.labels[index]

        if expected_name == "leaf":
            for index, label in enumerate(normalized_labels):
                if "leaf" in label and not label.startswith("non_"):
                    return self.labels[index]

        if expected_name == "non_leaf":
            for index, label in enumerate(normalized_labels):
                if "non_leaf" in label or label.startswith("non_"):
                    return self.labels[index]

        raise LeafVerifierInitializationError(f"Could not map '{expected_name}' from leaf verifier labels.")

    def preprocess(self, image: Image.Image) -> np.ndarray:
        """Convert an image into the ONNX input tensor format."""

        prepared_image = image.convert(self.color_mode)
        prepared_image = prepared_image.resize((self.input_size[1], self.input_size[0]))
        array = np.asarray(prepared_image, dtype=np.float32)

        if array.ndim != 3 or array.shape[2] != 3:
            raise LeafVerifierInferenceError("Uploaded image could not be prepared for leaf verification.")

        scale = float(self.config.get("preprocessing", {}).get("scale", 255.0))
        if scale <= 0:
            raise LeafVerifierInferenceError("Leaf verifier scale must be positive.")

        array = array / scale
        array = (array - self.mean) / self.std
        array = np.transpose(array, (2, 0, 1))
        return np.expand_dims(array, axis=0).astype(np.float32, copy=False)

    def predict(self, image: Image.Image) -> dict[str, Any]:
        """Run leaf verification and return the standardized response payload."""

        try:
            input_tensor = self.preprocess(image)
            raw_output = self.session.run(None, {self.input_name: input_tensor})[0]
        except LeafVerifierInferenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise LeafVerifierInferenceError("Leaf verification inference failed.") from exc

        logits = np.asarray(raw_output, dtype=np.float32).squeeze()
        probabilities = softmax(logits)
        top_index = int(np.argmax(probabilities))
        confidence = float(probabilities[top_index])
        predicted_label = self.labels[top_index] if top_index < len(self.labels) else str(top_index)
        normalized_label = predicted_label.lower()

        if confidence < self.confidence_threshold:
            verification = {
                "is_leaf": False,
                "status": "uncertain",
                "confidence": confidence,
                "predicted_class": "unknown",
            }
            pipeline = {"allow_processing": False, "next_step": "upload_again"}
            message = "Unable to verify the uploaded image. Please upload a clearer image."
        elif normalized_label == self.leaf_label.lower():
            verification = {
                "is_leaf": True,
                "status": "verified",
                "confidence": confidence,
                "predicted_class": self.leaf_label,
            }
            pipeline = {"allow_processing": True, "next_step": "disease_detection"}
            message = None
        else:
            verification = {
                "is_leaf": False,
                "status": "rejected",
                "confidence": confidence,
                "predicted_class": self.non_leaf_label,
            }
            pipeline = {"allow_processing": False, "next_step": "upload_again"}
            message = "Please upload a clear image of a single plant leaf."

        response: dict[str, Any] = {
            "success": True,
            "verification": verification,
            "pipeline": pipeline,
        }

        if message is not None:
            response["message"] = message

        return response