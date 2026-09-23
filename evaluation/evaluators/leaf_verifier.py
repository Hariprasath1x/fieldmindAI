"""Leaf verifier evaluator.

Dataset format expected in ``evaluation/data/leaf_verifier/``:
    leaf/
        img1.jpg ...
    non_leaf/
        img1.jpg ...
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image

from backend.services.leaf_verifier import LeafVerifier

logger = logging.getLogger("fieldmind.evaluation")


def evaluate(
    verifier: LeafVerifier,
    data_dir: Optional[Path] = None,
) -> dict[str, Any]:
    default_data_dir = (
        Path(__file__).resolve().parent.parent / "data" / "leaf_verifier"
    )
    eval_dir = data_dir or default_data_dir

    result: dict[str, Any] = {
        "model": "leaf_verifier",
        "model_name": "FieldMind Leaf Verification",
        "version": "1.0.0",
        "framework": "ONNX",
    }

    if not eval_dir.exists():
        result.update(
            {
                "dataset_available": False,
                "dataset_message": (
                    f"Evaluation dataset not found at '{eval_dir}'. "
                    "Provide a labelled dataset — see evaluation/data/README.md."
                ),
                "accuracy": None,
                "precision": None,
                "recall": None,
                "f1": None,
                "confusion_matrix": None,
            }
        )
        return result

    y_true: list[int] = []
    y_pred: list[int] = []
    # 0 = non_leaf, 1 = leaf
    label_map = {"non_leaf": 0, "leaf": 1}
    errors = 0

    t_start = time.perf_counter()

    for class_dir in sorted(eval_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        cls_name = class_dir.name.lower()
        if cls_name not in label_map:
            continue
        true_idx = label_map[cls_name]

        for img_path in class_dir.iterdir():
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            try:
                image = Image.open(img_path).convert("RGB")
                vr = verifier.predict(image)
                predicted_is_leaf = vr["verification"]["is_leaf"]
                pred_idx = 1 if predicted_is_leaf else 0
                y_true.append(true_idx)
                y_pred.append(pred_idx)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Skipping %s — %s", img_path.name, exc)
                errors += 1

    elapsed = round((time.perf_counter() - t_start) * 1000, 0)

    if not y_true:
        result.update(
            {
                "dataset_available": True,
                "dataset_message": "No valid images processed.",
                "accuracy": None,
                "precision": None,
                "recall": None,
                "f1": None,
                "errors": errors,
                "eval_time_ms": elapsed,
            }
        )
        return result

    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)

    accuracy = float(np.mean(y_true_arr == y_pred_arr))
    tp = int(np.sum((y_pred_arr == 1) & (y_true_arr == 1)))
    fp = int(np.sum((y_pred_arr == 1) & (y_true_arr == 0)))
    fn = int(np.sum((y_pred_arr == 0) & (y_true_arr == 1)))
    tn = int(np.sum((y_pred_arr == 0) & (y_true_arr == 0)))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    cm = [[tn, fp], [fn, tp]]
    result.update(
        {
            "dataset_available": True,
            "dataset_path": str(eval_dir),
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "confusion_matrix": cm,
            "confusion_matrix_labels": ["non_leaf", "leaf"],
            "sample_count": len(y_true),
            "errors": errors,
            "eval_time_ms": elapsed,
        }
    )
    return result
