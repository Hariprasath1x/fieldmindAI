"""Unit tests for disease progression calculation."""
from __future__ import annotations

import pytest

from backend.routers.diagnosis import _compute_progression
from backend.models.diagnosis_models import ProgressionStatus


def _make_record(
    diagnosis_id: str,
    timestamp: str,
    disease: str,
    confidence: float,
    affected_area_pct=None,
    plant_id: str = "plant-001",
) -> dict:
    return {
        "diagnosis_id": diagnosis_id,
        "timestamp": timestamp,
        "predicted_disease": disease,
        "confidence": confidence,
        "affected_area_pct": affected_area_pct,
        "plant_id": plant_id,
        "user_id": "user-1",
    }


class TestProgressionComputation:
    def test_single_record_returns_none(self):
        records = [_make_record("d1", "2026-01-01T00:00:00Z", "tomato_leaf_blight", 0.85)]
        result = _compute_progression(records)
        assert result is None

    def test_two_records_returns_summary(self):
        records = [
            _make_record("d1", "2026-01-01T00:00:00Z", "tomato_leaf_blight", 0.80, 8.0),
            _make_record("d2", "2026-01-08T00:00:00Z", "tomato_leaf_blight", 0.85, 17.0),
        ]
        result = _compute_progression(records)
        assert result is not None
        assert result.latest_status == ProgressionStatus.WORSENING
        assert result.area_delta_pct == pytest.approx(9.0, abs=0.01)

    def test_decreasing_area_is_improving(self):
        records = [
            _make_record("d1", "2026-01-01T00:00:00Z", "tomato_leaf_blight", 0.85, 20.0),
            _make_record("d2", "2026-01-08T00:00:00Z", "tomato_leaf_blight", 0.75, 8.0),
        ]
        result = _compute_progression(records)
        assert result is not None
        assert result.latest_status == ProgressionStatus.IMPROVING

    def test_stable_area_is_stable(self):
        records = [
            _make_record("d1", "2026-01-01T00:00:00Z", "tomato_leaf_blight", 0.85, 10.0),
            _make_record("d2", "2026-01-08T00:00:00Z", "tomato_leaf_blight", 0.83, 11.0),
        ]
        result = _compute_progression(records)
        assert result is not None
        assert result.latest_status == ProgressionStatus.STABLE

    def test_no_area_data_uses_confidence_fallback(self):
        """When affected_area_pct is None, should fall back to confidence trend."""
        records = [
            _make_record("d1", "2026-01-01T00:00:00Z", "tomato_leaf_blight", 0.65, None),
            _make_record("d2", "2026-01-08T00:00:00Z", "tomato_leaf_blight", 0.90, None),
        ]
        result = _compute_progression(records)
        assert result is not None
        assert result.area_delta_pct is None  # No area data
        assert result.latest_status in (ProgressionStatus.WORSENING, ProgressionStatus.STABLE)

    def test_progression_has_points(self):
        records = [
            _make_record("d1", "2026-01-01T00:00:00Z", "tomato_leaf_blight", 0.80, 8.0),
            _make_record("d2", "2026-01-08T00:00:00Z", "tomato_leaf_blight", 0.85, 17.0),
        ]
        result = _compute_progression(records)
        assert len(result.points) == 2
        assert result.points[0].affected_area_pct == 8.0
        assert result.points[1].affected_area_pct == 17.0

    def test_progression_sorted_by_timestamp(self):
        """Records out of order should be sorted by timestamp."""
        records = [
            _make_record("d2", "2026-01-08T00:00:00Z", "tomato_leaf_blight", 0.85, 17.0),
            _make_record("d1", "2026-01-01T00:00:00Z", "tomato_leaf_blight", 0.80, 8.0),
        ]
        result = _compute_progression(records)
        assert result is not None
        assert result.points[0].diagnosis_id == "d1"
        assert result.points[1].diagnosis_id == "d2"

    def test_message_is_non_empty(self):
        records = [
            _make_record("d1", "2026-01-01T00:00:00Z", "tomato_leaf_blight", 0.80, 8.0),
            _make_record("d2", "2026-01-08T00:00:00Z", "tomato_leaf_blight", 0.85, 17.0),
        ]
        result = _compute_progression(records)
        assert result.message
        assert len(result.message) > 0
