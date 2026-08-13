"""Crop recommendation model evaluator.

Dataset format: a CSV file at ``evaluation/data/crop_recommender/test.csv``
with columns: N, P, K, temperature, humidity, pH, rainfall, label

Computes:
    - Accuracy
    - Macro precision / recall / F1
    - Weighted F1
    - Top-3 accuracy (using predict_proba)
    - Confusion matrix
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

import numpy as np

logger = logging.getLogger("fieldmind.evaluation")

EXPECTED_COLUMNS = ["N", "P", "K", "temperature", "humidity", "pH", "rainfall", "label"]


def evaluate(crop_model: Any, data_dir: Optional[Path] = None) -> dict[str, Any]:
    default_csv = (
        Path(__file__).resolve().parent.parent / "data" / "crop_recommender" / "test.csv"
    )
    csv_path = (data_dir / "test.csv") if data_dir else default_csv

    result: dict[str, Any] = {
        "model": "crop_recommender",
        "model_name": "crop_model.pkl",
        "version": "1.0.0",
        "framework": "scikit-learn",
    }

    if not csv_path.exists():
        result.update(
            {
                "dataset_available": False,
                "dataset_message": (
                    f"Evaluation CSV not found at '{csv_path}'. "
                    "Provide a CSV with columns: N,P,K,temperature,humidity,pH,rainfall,label. "
                    "See evaluation/data/README.md."
                ),
                "accuracy": None,
                "macro_f1": None,
                "top_3_accuracy": None,
            }
        )
        return result

    try:
        import csv

        rows = []
        with csv_path.open("r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                rows.append(row)

        if not rows:
            result.update(
                {
                    "dataset_available": True,
                    "dataset_message": "CSV file is empty.",
                    "accuracy": None,
                    "macro_f1": None,
                }
            )
            return result

        features = []
        labels = []
        for row in rows:
            try:
                features.append(
                    [
                        float(row["N"]),
                        float(row["P"]),
                        float(row["K"]),
                        float(row["temperature"]),
                        float(row["humidity"]),
                        float(row.get("pH", row.get("ph", 0))),
                        float(row["rainfall"]),
                    ]
                )
                labels.append(row["label"].strip())
            except (KeyError, ValueError) as exc:
                logger.debug("Skipping malformed row: %s", exc)

        X = np.array(features, dtype=np.float32)
        classes = list(crop_model.classes_)
        class_to_idx = {c: i for i, c in enumerate(classes)}
        n_classes = len(classes)

        t_start = time.perf_counter()
        predictions = crop_model.predict(X)
        top3_correct: list[bool] = []

        if hasattr(crop_model, "predict_proba"):
            probas = crop_model.predict_proba(X)
            top3_indices = np.argsort(probas, axis=1)[:, ::-1][:, :3]
            true_indices = [class_to_idx.get(lbl, -1) for lbl in labels]
            for true_idx, top3 in zip(true_indices, top3_indices):
                top3_correct.append(true_idx in top3)

        elapsed = round((time.perf_counter() - t_start) * 1000, 0)

        y_true = [class_to_idx.get(lbl, -1) for lbl in labels]
        y_pred = [class_to_idx.get(str(p), -1) for p in predictions]

        y_true_arr = np.array(y_true)
        y_pred_arr = np.array(y_pred)
        accuracy = float(np.mean(y_true_arr == y_pred_arr))

        cm = np.zeros((n_classes, n_classes), dtype=int)
        for t, p in zip(y_true, y_pred):
            if 0 <= t < n_classes and 0 <= p < n_classes:
                cm[t][p] += 1

        macro_f1 = 0.0
        for ci in range(n_classes):
            tp = int(cm[ci, ci])
            fp = int(cm[:, ci].sum()) - tp
            fn = int(cm[ci, :].sum()) - tp
            p_ = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            r_ = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * p_ * r_ / (p_ + r_) if (p_ + r_) > 0 else 0.0
            macro_f1 += f1
        macro_f1 /= n_classes

        result.update(
            {
                "dataset_available": True,
                "dataset_path": str(csv_path),
                "accuracy": round(accuracy, 4),
                "macro_f1": round(macro_f1, 4),
                "top_3_accuracy": (
                    round(float(np.mean(top3_correct)), 4) if top3_correct else None
                ),
                "sample_count": len(y_true),
                "class_count": n_classes,
                "confusion_matrix": cm.tolist(),
                "confusion_matrix_labels": classes,
                "eval_time_ms": elapsed,
            }
        )

    except Exception as exc:  # noqa: BLE001
        logger.error("Crop recommender evaluation failed: %s", exc, exc_info=True)
        result.update(
            {
                "dataset_available": True,
                "dataset_message": f"Evaluation failed: {exc}",
                "accuracy": None,
                "macro_f1": None,
            }
        )

    return result
