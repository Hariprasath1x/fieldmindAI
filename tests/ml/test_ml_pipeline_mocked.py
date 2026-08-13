"""ML pipeline tests using mocked models."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np

from tests.conftest import (
    image_to_bytes,
    make_blurry_image,
    make_green_image,
)


class TestInferencePipelineStages:
    def test_leaf_rejected_stops_pipeline(self, mock_leaf_verifier_reject):
        """When leaf verifier rejects, disease classification must NOT run."""
        from backend.worker.inference_worker import run_inference_job
        from backend.db.firebase import get_db

        db = get_db()
        import uuid
        from datetime import datetime, timezone
        job_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc).isoformat()
        db.collection("inference_jobs").document(job_id).set({
            "job_id": job_id, "status": "queued",
            "user_id": None, "plant_id": None, "field_id": None,
            "request_id": "test", "created_at": now, "updated_at": now,
            "result": None, "error": None,
        })

        image_bytes = image_to_bytes(make_green_image())

        with patch("backend.worker.inference_worker.inference_service") as mock_svc:
            result = run_inference_job(
                job_id=job_id,
                image_bytes=image_bytes,
                content_type="image/jpeg",
                filename="leaf.jpg",
                user_id=None,
                plant_id=None,
                field_id=None,
                leaf_verifier=mock_leaf_verifier_reject,
            )

        # Disease classifier should NOT have been called
        mock_svc.run_classifier.assert_not_called()
        assert result["status"] == "rejected"

    def test_blurry_image_fails_before_leaf_verification(self):
        """Image validation should fail for blurry images before leaf verification runs."""
        from backend.worker.inference_worker import run_inference_job
        from backend.db.firebase import get_db

        db = get_db()
        import uuid
        from datetime import datetime, timezone
        job_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc).isoformat()
        db.collection("inference_jobs").document(job_id).set({
            "job_id": job_id, "status": "queued",
            "user_id": None, "plant_id": None, "field_id": None,
            "request_id": "test", "created_at": now, "updated_at": now,
            "result": None, "error": None,
        })

        blurry_bytes = image_to_bytes(make_blurry_image())
        mock_lv = MagicMock()

        with patch("backend.worker.inference_worker.inference_service"):
            result = run_inference_job(
                job_id=job_id,
                image_bytes=blurry_bytes,
                content_type="image/jpeg",
                filename="blurry.jpg",
                user_id=None,
                plant_id=None,
                field_id=None,
                leaf_verifier=mock_lv,
            )

        assert not result["success"]
        assert result["stage_failed"] == "image_validation"
        # Leaf verifier should NOT have been called
        mock_lv.predict.assert_not_called()

    def test_high_confidence_triggers_yolo(self, mock_inference_service, mock_leaf_verifier):
        """High confidence classifier result should trigger YOLO."""
        from backend.worker.inference_worker import run_inference_job
        from backend.db.firebase import get_db

        db = get_db()
        import uuid
        from datetime import datetime, timezone
        job_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc).isoformat()
        db.collection("inference_jobs").document(job_id).set({
            "job_id": job_id, "status": "queued",
            "user_id": None, "plant_id": None, "field_id": None,
            "request_id": "test", "created_at": now, "updated_at": now,
            "result": None, "error": None,
        })

        image_bytes = image_to_bytes(make_green_image())
        # confidence = 0.85 → HIGH → should trigger YOLO
        mock_inference_service.run_classifier.return_value = (
            "cashew_anthracnose", 0.85, np.array([0.85, 0.05, 0.05, 0.05])
        )

        with patch("backend.worker.inference_worker.inference_service", mock_inference_service):
            result = run_inference_job(
                job_id=job_id,
                image_bytes=image_bytes,
                content_type="image/jpeg",
                filename="leaf.jpg",
                user_id=None,
                plant_id=None,
                field_id=None,
                leaf_verifier=mock_leaf_verifier,
            )

        mock_inference_service.run_yolo.assert_called_once()
        assert result["success"]
        assert result["confidence_level"] == "high"

    def test_low_confidence_skips_yolo(self, mock_inference_service, mock_leaf_verifier):
        """Low confidence result must NOT run YOLO."""
        from backend.worker.inference_worker import run_inference_job
        from backend.db.firebase import get_db

        db = get_db()
        import uuid
        from datetime import datetime, timezone
        job_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc).isoformat()
        db.collection("inference_jobs").document(job_id).set({
            "job_id": job_id, "status": "queued",
            "user_id": None, "plant_id": None, "field_id": None,
            "request_id": "test", "created_at": now, "updated_at": now,
            "result": None, "error": None,
        })

        image_bytes = image_to_bytes(make_green_image())
        # confidence = 0.20 → LOW → should NOT trigger YOLO
        mock_inference_service.run_classifier.return_value = (
            "cashew_anthracnose", 0.20, np.array([0.20, 0.30, 0.30, 0.20])
        )

        with patch("backend.worker.inference_worker.inference_service", mock_inference_service):
            result = run_inference_job(
                job_id=job_id,
                image_bytes=image_bytes,
                content_type="image/jpeg",
                filename="leaf.jpg",
                user_id=None,
                plant_id=None,
                field_id=None,
                leaf_verifier=mock_leaf_verifier,
            )

        mock_inference_service.run_yolo.assert_not_called()
        assert result["confidence_level"] == "low"


class TestMLPipelineErrorHandling:
    def test_yolo_failure_does_not_crash_pipeline(self, mock_inference_service, mock_leaf_verifier):
        """YOLO failure should be logged but not propagate as a fatal error."""
        from backend.worker.inference_worker import run_inference_job
        from backend.db.firebase import get_db

        db = get_db()
        import uuid
        from datetime import datetime, timezone
        job_id = str(uuid.uuid4())
        now = datetime.now(tz=timezone.utc).isoformat()
        db.collection("inference_jobs").document(job_id).set({
            "job_id": job_id, "status": "queued",
            "user_id": None, "plant_id": None, "field_id": None,
            "request_id": "test", "created_at": now, "updated_at": now,
            "result": None, "error": None,
        })

        image_bytes = image_to_bytes(make_green_image())
        mock_inference_service.run_classifier.return_value = (
            "cashew_anthracnose", 0.85, np.array([0.85, 0.05, 0.05, 0.05])
        )
        mock_inference_service.run_yolo.side_effect = RuntimeError("YOLO model crashed")

        with patch("backend.worker.inference_worker.inference_service", mock_inference_service):
            result = run_inference_job(
                job_id=job_id,
                image_bytes=image_bytes,
                content_type="image/jpeg",
                filename="leaf.jpg",
                user_id=None,
                plant_id=None,
                field_id=None,
                leaf_verifier=mock_leaf_verifier,
            )

        # Pipeline should complete despite YOLO failure
        assert result["success"]
        # YOLO detections should be empty
        assert result["severity"]["detections"] == []
