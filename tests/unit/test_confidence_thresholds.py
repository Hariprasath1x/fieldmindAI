"""Unit tests for confidence threshold logic."""
from __future__ import annotations



from backend.core.config import Settings
from backend.worker.inference_worker import _confidence_level, _build_recommendation
from backend.models.diagnosis_models import ConfidenceLevel


class TestConfidenceLevel:
    def test_high_confidence(self):
        level = _confidence_level(0.90)
        assert level == ConfidenceLevel.HIGH

    def test_exactly_at_high_threshold(self):
        # Boundary: >= HIGH threshold
        level = _confidence_level(0.75)
        assert level == ConfidenceLevel.HIGH

    def test_medium_confidence(self):
        level = _confidence_level(0.60)
        assert level == ConfidenceLevel.MEDIUM

    def test_exactly_at_medium_threshold(self):
        level = _confidence_level(0.45)
        assert level == ConfidenceLevel.MEDIUM

    def test_low_confidence(self):
        level = _confidence_level(0.30)
        assert level == ConfidenceLevel.LOW

    def test_zero_confidence_is_low(self):
        level = _confidence_level(0.0)
        assert level == ConfidenceLevel.LOW

    def test_just_below_medium_is_low(self):
        level = _confidence_level(0.44)
        assert level == ConfidenceLevel.LOW

    def test_just_below_high_is_medium(self):
        level = _confidence_level(0.74)
        assert level == ConfidenceLevel.MEDIUM


class TestBuildRecommendation:
    def test_low_confidence_returns_uncertainty_message(self):
        rec = _build_recommendation("cashew_anthracnose", ConfidenceLevel.LOW, [])
        assert "confidently" in rec.lower() or "could not" in rec.lower()

    def test_medium_confidence_includes_tentative(self):
        rec = _build_recommendation("cashew_anthracnose", ConfidenceLevel.MEDIUM, [])
        assert "tentative" in rec.lower() or "moderate" in rec.lower()

    def test_high_confidence_no_detections(self):
        rec = _build_recommendation("cashew_anthracnose", ConfidenceLevel.HIGH, [])
        assert "cashew_anthracnose" in rec.lower()

    def test_high_confidence_with_detections(self):
        detections = [{"label": "anthracnose", "confidence": 0.82, "box": [10, 10, 50, 50]}]
        rec = _build_recommendation("cashew_anthracnose", ConfidenceLevel.HIGH, detections)
        assert "anthracnose" in rec.lower()

    def test_low_confidence_never_claims_certainty(self):
        rec = _build_recommendation("cashew_anthracnose", ConfidenceLevel.LOW, [
            {"label": "anthracnose", "confidence": 0.82, "box": [10, 10, 50, 50]}
        ])
        # Even with YOLO detections, low classifier confidence should NOT give a definitive diagnosis
        # The recommendation should express uncertainty
        assert any(word in rec.lower() for word in ["could not", "confidently", "clearer", "uncertain"])


class TestSettings:
    def test_settings_singleton(self):
        from backend.core.config import get_settings, settings
        assert get_settings() is settings

    def test_threshold_ordering(self):
        s = Settings()
        assert s.DISEASE_MEDIUM_CONFIDENCE_THRESHOLD < s.DISEASE_HIGH_CONFIDENCE_THRESHOLD

    def test_max_image_size_bytes(self):
        s = Settings()
        assert s.max_image_size_bytes == int(s.MAX_IMAGE_SIZE_MB * 1024 * 1024)

    def test_positive_thresholds(self):
        s = Settings()
        assert s.LEAF_VERIFICATION_THRESHOLD > 0
        assert s.DISEASE_HIGH_CONFIDENCE_THRESHOLD > 0
        assert s.IMAGE_BLUR_THRESHOLD > 0
        assert s.MAX_IMAGE_SIZE_MB > 0
