"""Unit tests for feedback validation."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.models.diagnosis_models import FeedbackCreate, FeedbackType


class TestFeedbackValidation:
    def test_valid_correct_feedback(self):
        f = FeedbackCreate(
            prediction_id="diag-001",
            user_id="user-001",
            predicted_label="cashew_anthracnose",
            feedback_type=FeedbackType.CORRECT,
        )
        assert f.feedback_type == FeedbackType.CORRECT
        assert f.actual_label is None

    def test_valid_incorrect_feedback_with_correction(self):
        f = FeedbackCreate(
            prediction_id="diag-001",
            user_id="user-001",
            predicted_label="cashew_anthracnose",
            actual_label="cashew_healthy",
            feedback_type=FeedbackType.INCORRECT,
        )
        assert f.actual_label == "cashew_healthy"

    def test_incorrect_feedback_without_actual_label_is_valid(self):
        """actual_label is optional even for incorrect feedback."""
        f = FeedbackCreate(
            prediction_id="diag-001",
            user_id="user-001",
            predicted_label="cashew_anthracnose",
            feedback_type=FeedbackType.INCORRECT,
        )
        assert f.actual_label is None

    def test_feedback_type_enum_validation(self):
        with pytest.raises((ValidationError, ValueError)):
            FeedbackCreate(
                prediction_id="diag-001",
                user_id="user-001",
                predicted_label="cashew_anthracnose",
                feedback_type="maybe",  # invalid value
            )

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            FeedbackCreate(
                user_id="user-001",
                feedback_type=FeedbackType.CORRECT,
                # Missing prediction_id and predicted_label
            )

    def test_model_dump_has_all_fields(self):
        f = FeedbackCreate(
            prediction_id="diag-001",
            user_id="user-001",
            predicted_label="cashew_anthracnose",
            feedback_type=FeedbackType.CORRECT,
        )
        d = f.model_dump()
        assert "prediction_id" in d
        assert "user_id" in d
        assert "predicted_label" in d
        assert "feedback_type" in d
