"""YOLO severity model evaluator.

Computes detection metrics including Precision, Recall, and mAP.

Dataset format: YOLO-format annotation files at
    ``evaluation/data/yolo_detector/``
        images/
            img1.jpg ...
        labels/
            img1.txt   (one line per box: class cx cy w h — normalised)

NOTE: Without a labelled detection dataset this evaluator returns null metrics.
The mAP computation uses a lightweight pure-NumPy implementation.
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


def _iou(boxA: list[float], boxB: list[float]) -> float:
    x1 = max(boxA[0], boxB[0])
    y1 = max(boxA[1], boxB[1])
    x2 = min(boxA[2], boxB[2])
    y2 = min(boxA[3], boxB[3])
    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    aA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    aB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    union = aA + aB - inter
    return inter / union if union > 0 else 0.0


def _average_precision(recalls: list[float], precisions: list[float]) -> float:
    """Compute AP using 11-point interpolation."""
    ap = 0.0
    for t in np.linspace(0, 1, 11):
        p_values = [p for r, p in zip(recalls, precisions) if r >= t]
        ap += max(p_values) if p_values else 0.0
    return ap / 11.0


def evaluate(
    service: MLInferenceService,
    data_dir: Optional[Path] = None,
    iou_threshold: float = 0.5,
) -> dict[str, Any]:
    default_data_dir = (
        Path(__file__).resolve().parent.parent / "data" / "yolo_detector"
    )
    eval_dir = data_dir or default_data_dir

    result: dict[str, Any] = {
        "model": "yolo_detector",
        "model_name": "fieldmind_yolo_best.onnx",
        "version": "1.0.0",
        "framework": "ONNX / YOLOv8",
        "iou_threshold": iou_threshold,
    }

    images_dir = eval_dir / "images"
    labels_dir = eval_dir / "labels"

    if not eval_dir.exists() or not images_dir.exists() or not labels_dir.exists():
        result.update(
            {
                "dataset_available": False,
                "dataset_message": (
                    f"Evaluation dataset not found at '{eval_dir}'. "
                    "Provide YOLO-format annotations — see evaluation/data/README.md."
                ),
                "precision": None,
                "recall": None,
                "map_50": None,
                "map_50_95": None,
            }
        )
        return result

    # Per-class: list of (confidence, is_tp)
    per_class_preds: dict[str, list[tuple[float, bool]]] = {}
    per_class_gt_count: dict[str, int] = {}
    total_images = 0
    errors = 0
    yolo_classes = service.yolo_class_names

    t_start = time.perf_counter()

    for img_path in sorted(images_dir.iterdir()):
        if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
            continue
        label_path = labels_dir / (img_path.stem + ".txt")
        if not label_path.exists():
            continue

        total_images += 1

        try:
            image = Image.open(img_path).convert("RGB")
            iw, ih = image.size

            # Parse ground truth
            gt_boxes: list[dict] = []
            with label_path.open() as fh:
                for line in fh:
                    parts = line.strip().split()
                    if len(parts) != 5:
                        continue
                    cls_idx, cx, cy, bw, bh = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                    x1 = (cx - bw / 2) * iw
                    y1 = (cy - bh / 2) * ih
                    x2 = (cx + bw / 2) * iw
                    y2 = (cy + bh / 2) * ih
                    cls_name = yolo_classes[cls_idx] if cls_idx < len(yolo_classes) else str(cls_idx)
                    gt_boxes.append({"class": cls_name, "box": [x1, y1, x2, y2], "used": False})
                    per_class_gt_count[cls_name] = per_class_gt_count.get(cls_name, 0) + 1

            # Run inference
            predictions = service.run_yolo(image)

            # Match predictions to GT at iou_threshold
            for pred in sorted(predictions, key=lambda d: d["confidence"], reverse=True):
                cls_name = pred["label"]
                conf = pred["confidence"]
                pred_box = pred["box"]

                if cls_name not in per_class_preds:
                    per_class_preds[cls_name] = []

                # Find best matching GT box
                best_iou = 0.0
                best_gt_idx = -1
                for gi, gt in enumerate(gt_boxes):
                    if gt["class"] != cls_name or gt["used"]:
                        continue
                    iou_val = _iou(pred_box, gt["box"])
                    if iou_val > best_iou:
                        best_iou = iou_val
                        best_gt_idx = gi

                if best_iou >= iou_threshold and best_gt_idx >= 0:
                    gt_boxes[best_gt_idx]["used"] = True
                    per_class_preds[cls_name].append((conf, True))
                else:
                    per_class_preds[cls_name].append((conf, False))

        except Exception as exc:  # noqa: BLE001
            logger.debug("Error processing %s: %s", img_path.name, exc)
            errors += 1

    elapsed = round((time.perf_counter() - t_start) * 1000, 0)

    if total_images == 0:
        result.update(
            {
                "dataset_available": True,
                "dataset_message": "No valid image/label pairs found.",
                "precision": None,
                "recall": None,
                "map_50": None,
                "map_50_95": None,
                "errors": errors,
                "eval_time_ms": elapsed,
            }
        )
        return result

    # Compute per-class AP and aggregate
    all_aps: list[float] = []
    per_class_metrics: dict[str, dict] = {}

    for cls_name, preds in per_class_preds.items():
        preds_sorted = sorted(preds, key=lambda x: x[0], reverse=True)
        tp_cumsum = 0
        fp_cumsum = 0
        recalls = []
        precisions = []
        n_gt = per_class_gt_count.get(cls_name, 0)

        for conf, is_tp in preds_sorted:
            if is_tp:
                tp_cumsum += 1
            else:
                fp_cumsum += 1
            r = tp_cumsum / n_gt if n_gt > 0 else 0.0
            p = tp_cumsum / (tp_cumsum + fp_cumsum)
            recalls.append(r)
            precisions.append(p)

        ap = _average_precision(recalls, precisions)
        all_aps.append(ap)

        final_p = precisions[-1] if precisions else 0.0
        final_r = recalls[-1] if recalls else 0.0
        per_class_metrics[cls_name] = {
            "ap_50": round(ap, 4),
            "precision": round(final_p, 4),
            "recall": round(final_r, 4),
            "gt_count": n_gt,
        }

    map_50 = float(np.mean(all_aps)) if all_aps else 0.0

    # mAP@50:95 — run at multiple thresholds
    map_50_95_values: list[float] = []
    for thresh in np.arange(0.5, 1.0, 0.05):
        # Simplified: scale AP by IoU overlap (full re-run would be needed for accuracy)
        # We approximate as map_50 * (1 - (thresh - 0.5))
        # NOTE: This is an approximation. For exact mAP@50:95, re-run evaluation
        # at each threshold. A proper dataset-based evaluation is preferred.
        map_50_95_values.append(map_50 * (1.0 - (float(thresh) - 0.5) * 1.2))
    map_50_95 = max(0.0, float(np.mean(map_50_95_values)))

    # Overall precision and recall
    all_preds_flat = [p for preds in per_class_preds.values() for p in preds]
    overall_tp = sum(1 for _, tp in all_preds_flat if tp)
    overall_fp = len(all_preds_flat) - overall_tp
    total_gt = sum(per_class_gt_count.values())
    overall_precision = overall_tp / (overall_tp + overall_fp) if (overall_tp + overall_fp) > 0 else 0.0
    overall_recall = overall_tp / total_gt if total_gt > 0 else 0.0

    result.update(
        {
            "dataset_available": True,
            "dataset_path": str(eval_dir),
            "precision": round(overall_precision, 4),
            "recall": round(overall_recall, 4),
            "map_50": round(map_50, 4),
            "map_50_95": round(map_50_95, 4),
            "map_50_95_note": "Approximated via linear decay from mAP@50. For exact mAP@50:95 provide per-threshold re-evaluation.",
            "per_class": per_class_metrics,
            "total_images": total_images,
            "errors": errors,
            "eval_time_ms": elapsed,
        }
    )
    return result
