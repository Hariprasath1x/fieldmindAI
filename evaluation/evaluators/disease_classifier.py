"""Disease classifier evaluator.

Computes:
    - Top-1 accuracy
    - Top-3 accuracy
    - Per-class precision, recall, F1
    - Macro / weighted F1
    - Confusion matrix

NOTE: Metrics are only computed when a labelled evaluation dataset is
provided.  Without a dataset this evaluator returns null metrics and a clear
message explaining why, rather than fabricating numbers.

Dataset format expected in ``evaluation/data/disease_classifier/``:
    <class_name>/
        image1.jpg
        image2.png
        ...

Each subdirectory name must exactly match a class name in ``class_names.json``.
"""
from __future__ import annotations


import logging
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image

from backend.services.ml_inference import MLInferenceService

logger = logging.getLogger("fieldmind.evaluation")


def _compute_metrics(
    y_true: list[int],
    y_pred: list[int],
    top3_correct: list[bool],
    class_names: list[str],
) -> dict[str, Any]:
    """Pure NumPy metric computation (no scikit-learn required at evaluation time)."""
    n_classes = len(class_names)
    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)

    top1_acc = float(np.mean(y_true_arr == y_pred_arr))
    top3_acc = float(np.mean(top3_correct))

    # Per-class metrics
    per_class: dict[str, dict[str, float]] = {}
    macro_precision = macro_recall = macro_f1 = 0.0
    weighted_f1 = 0.0
    total = len(y_true)

    # Confusion matrix
    cm = np.zeros((n_classes, n_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        if 0 <= t < n_classes and 0 <= p < n_classes:
            cm[t][p] += 1

    for cls_idx, cls_name in enumerate(class_names):
        tp = int(cm[cls_idx, cls_idx])
        fp = int(cm[:, cls_idx].sum()) - tp
        fn = int(cm[cls_idx, :].sum()) - tp
        support = int(cm[cls_idx, :].sum())

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        per_class[cls_name] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support,
        }

        macro_precision += precision
        macro_recall += recall
        macro_f1 += f1
        weighted_f1 += f1 * support

    macro_precision /= n_classes
    macro_recall /= n_classes
    macro_f1 /= n_classes
    weighted_f1 /= total if total > 0 else 1

    return {
        "top_1_accuracy": round(top1_acc, 4),
        "top_3_accuracy": round(top3_acc, 4),
        "accuracy": round(top1_acc, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "confusion_matrix_labels": class_names,
        "sample_count": total,
    }


def evaluate(
    service: MLInferenceService,
    data_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """Run the disease classifier evaluation.

    Args:
        service:  Initialised MLInferenceService.
        data_dir: Path to the evaluation dataset directory.
                  If None or doesn't exist, returns a dataset-missing result.

    Returns:
        Dict with model metadata and metrics (or null metrics with explanation).
    """
    result: dict[str, Any] = {
        "model": "disease_classifier",
        "model_name": service.classifier_model_name,
        "version": service.classifier_model_version,
        "framework": "ONNX",
        "class_count": len(service.class_names),
    }

    default_data_dir = (
        Path(__file__).resolve().parent.parent / "data" / "disease_classifier"
    )
    eval_dir = data_dir or default_data_dir

    if not eval_dir.exists():
        result.update(
            {
                "dataset_available": False,
                "dataset_message": (
                    f"Evaluation dataset not found at '{eval_dir}'. "
                    "Provide a labelled dataset — see evaluation/data/README.md. "
                    "No metrics are fabricated."
                ),
                "accuracy": None,
                "macro_f1": None,
                "top_1_accuracy": None,
                "top_3_accuracy": None,
                "per_class": None,
                "confusion_matrix": None,
            }
        )
        return result

    class_names = service.class_names
    class_to_idx = {name: i for i, name in enumerate(class_names)}

    y_true: list[int] = []
    y_pred: list[int] = []
    top3_correct: list[bool] = []
    errors = 0

    logger.info("Evaluating disease classifier on dataset at %s", eval_dir)
    t_start = time.perf_counter()

    for class_dir in sorted(eval_dir.iterdir()):
        if not class_dir.is_dir():
            continue
        cls_name = class_dir.name
        if cls_name not in class_to_idx:
            logger.warning("Class '%s' in dataset not in model classes — skipping.", cls_name)
            continue
        true_idx = class_to_idx[cls_name]

        for img_path in class_dir.iterdir():
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
                continue
            try:
                image = Image.open(img_path).convert("RGB")
                label, conf, probs = service.run_classifier(image)

                pred_idx = class_names.index(label) if label in class_names else -1
                top3_indices = np.argsort(probs)[::-1][:3]

                y_true.append(true_idx)
                y_pred.append(pred_idx)
                top3_correct.append(true_idx in top3_indices)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Skipping %s — %s", img_path.name, exc)
                errors += 1

    elapsed = round((time.perf_counter() - t_start) * 1000, 0)

    if not y_true:
        result.update(
            {
                "dataset_available": True,
                "dataset_message": "Dataset directory exists but no valid images were processed.",
                "accuracy": None,
                "macro_f1": None,
                "top_1_accuracy": None,
                "top_3_accuracy": None,
                "per_class": None,
                "confusion_matrix": None,
                "errors": errors,
                "eval_time_ms": elapsed,
            }
        )
        return result

    metrics = _compute_metrics(y_true, y_pred, top3_correct, class_names)
    result.update(
        {
            "dataset_available": True,
            "dataset_path": str(eval_dir),
            "errors": errors,
            "eval_time_ms": elapsed,
            **metrics,
        }
    )
    return result
