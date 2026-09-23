"""Main evaluation entry point.

Usage:
    python -m evaluation.evaluate [--models-dir PATH] [--output-dir PATH]

Runs all four evaluators and writes results to ``evaluation/results/``.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.core.logging_config import configure_logging
from backend.core.config import settings
from backend.services.ml_inference import MLInferenceService
from backend.services.leaf_verifier import LeafVerifier

from evaluation.evaluators import disease_classifier, leaf_verifier, yolo_detector, crop_recommender

configure_logging(level="INFO", json_format=False)
logger = logging.getLogger("fieldmind.evaluation")


def _resolve_models_dir(override: str | None) -> Path:
    if override:
        return Path(override)
    dir_ = settings.MODELS_DIR
    if not dir_.is_absolute():
        return Path(__file__).resolve().parent.parent / dir_
    return dir_


def _save_result(result: dict, output_dir: Path, model_name: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"{model_name}_{ts}.json"
    path = output_dir / filename
    with path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
    return path


def _print_summary(result: dict) -> None:
    model = result.get("model", "unknown")
    print(f"\n{'='*60}")
    print(f"  {model.upper()}")
    print(f"{'='*60}")

    if not result.get("dataset_available", True):
        print(f"  ⚠  {result.get('dataset_message', 'Dataset not available.')}")
        return

    fields = [
        ("Accuracy", "accuracy"),
        ("Macro F1", "macro_f1"),
        ("Top-1 Accuracy", "top_1_accuracy"),
        ("Top-3 Accuracy", "top_3_accuracy"),
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("F1", "f1"),
        ("mAP@50", "map_50"),
        ("mAP@50:95", "map_50_95"),
        ("Sample Count", "sample_count"),
    ]
    for label, key in fields:
        value = result.get(key)
        if value is not None:
            if isinstance(value, float):
                print(f"  {label:<20} {value:.4f}")
            else:
                print(f"  {label:<20} {value}")


def main() -> None:
    parser = argparse.ArgumentParser(description="FieldMind ML evaluation pipeline")
    parser.add_argument("--models-dir", default=None, help="Override models directory")
    parser.add_argument(
        "--output-dir",
        default="evaluation/results",
        help="Directory to save JSON results",
    )
    parser.add_argument(
        "--models",
        nargs="*",
        choices=["disease", "leaf", "yolo", "crop", "all"],
        default=["all"],
        help="Which models to evaluate",
    )
    args = parser.parse_args()

    models_dir = _resolve_models_dir(args.models_dir)
    output_dir = Path(args.output_dir)
    run_all = "all" in args.models
    to_evaluate = args.models if not run_all else ["disease", "leaf", "yolo", "crop"]

    print(f"\nFieldMind ML Evaluation Pipeline")
    print(f"Models directory: {models_dir}")
    print(f"Results directory: {output_dir}")
    print(f"Timestamp: {datetime.now(tz=timezone.utc).isoformat()}")

    # Initialise ML service
    svc = MLInferenceService()
    try:
        svc.initialise(models_dir)
        logger.info("ML service initialised successfully.")
    except Exception as exc:
        logger.error("Failed to initialise ML service: %s", exc)
        print(f"\n✗ Could not load ML models from {models_dir}. Check the path.")
        sys.exit(1)

    # Initialise leaf verifier
    lv: LeafVerifier | None = None
    if "leaf" in to_evaluate:
        try:
            def _res(name: str) -> Path:
                candidates = [
                    Path(__file__).resolve().parent.parent / "backend" / "models" / name,
                    models_dir / name,
                ]
                for c in candidates:
                    if c.exists():
                        return c
                raise FileNotFoundError(name)

            lv = LeafVerifier(
                model_path=_res("leaf_verifier.onnx"),
                config_path=_res("leaf_verifier_config.json"),
                labels_path=_res("labels.json"),
            )
        except Exception as exc:
            logger.warning("Leaf verifier unavailable: %s", exc)

    all_results: list[dict] = []
    timestamp = datetime.now(tz=timezone.utc).isoformat()

    if "disease" in to_evaluate:
        print("\n[1/4] Evaluating disease classifier...")
        res = disease_classifier.evaluate(svc)
        res["evaluation_timestamp"] = timestamp
        path = _save_result(res, output_dir, "disease_classifier")
        print(f"  Saved → {path}")
        _print_summary(res)
        all_results.append(res)

    if "leaf" in to_evaluate and lv is not None:
        print("\n[2/4] Evaluating leaf verifier...")
        res = leaf_verifier.evaluate(lv)
        res["evaluation_timestamp"] = timestamp
        path = _save_result(res, output_dir, "leaf_verifier")
        print(f"  Saved → {path}")
        _print_summary(res)
        all_results.append(res)
    elif "leaf" in to_evaluate:
        print("\n[2/4] Leaf verifier skipped — model not loaded.")

    if "yolo" in to_evaluate:
        print("\n[3/4] Evaluating YOLO detector...")
        res = yolo_detector.evaluate(svc)
        res["evaluation_timestamp"] = timestamp
        path = _save_result(res, output_dir, "yolo_detector")
        print(f"  Saved → {path}")
        _print_summary(res)
        all_results.append(res)

    if "crop" in to_evaluate:
        print("\n[4/4] Evaluating crop recommender...")
        res = crop_recommender.evaluate(svc.crop_model)
        res["evaluation_timestamp"] = timestamp
        path = _save_result(res, output_dir, "crop_recommender")
        print(f"  Saved → {path}")
        _print_summary(res)
        all_results.append(res)

    # Save combined summary
    summary = {
        "evaluation_timestamp": timestamp,
        "models_dir": str(models_dir),
        "results": all_results,
    }
    summary_path = _save_result(summary, output_dir, "summary")
    print(f"\n✓ Summary saved → {summary_path}")
    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()
