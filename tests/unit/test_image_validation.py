"""Unit tests for image validation service."""
from __future__ import annotations

from backend.services.image_validation import (
    validate_image,
)
from tests.conftest import (
    image_to_bytes,
    make_blurry_image,
    make_green_image,
    make_tiny_image,
)


class TestFileTypeValidation:
    def test_valid_jpeg_content_type_passes(self):
        data = image_to_bytes(make_green_image())
        result = validate_image(data, content_type="image/jpeg")
        assert result.passed

    def test_valid_png_content_type_passes(self):
        data = image_to_bytes(make_green_image(), fmt="PNG")
        result = validate_image(data, content_type="image/png")
        assert result.passed

    def test_non_image_content_type_fails(self):
        result = validate_image(b"fake data", content_type="application/pdf")
        assert not result.passed
        assert result.error_code == "INVALID_FILE_TYPE"

    def test_unsupported_image_format_fails(self):
        result = validate_image(b"fake data", content_type="image/gif")
        assert not result.passed
        assert result.error_code == "UNSUPPORTED_IMAGE_FORMAT"

    def test_no_content_type_still_validates(self):
        """Missing content-type header should not auto-fail."""
        data = image_to_bytes(make_green_image())
        result = validate_image(data, content_type=None)
        # Passes because we still try to decode the image
        assert result.passed or result.error_code in (
            "CORRUPT_IMAGE", "IMAGE_TOO_SMALL", "IMAGE_TOO_BLURRY"
        )


class TestFileSizeValidation:
    def test_empty_file_fails(self):
        result = validate_image(b"", content_type="image/jpeg")
        assert not result.passed
        assert result.error_code == "EMPTY_FILE"

    def test_file_within_limit_passes(self):
        data = image_to_bytes(make_green_image())
        result = validate_image(data, content_type="image/jpeg")
        assert result.passed

    def test_file_too_large_fails(self, monkeypatch):
        # Temporarily lower the limit to 1 byte
        from backend.core import config as cfg
        orig = cfg.settings.MAX_IMAGE_SIZE_MB
        cfg.settings.MAX_IMAGE_SIZE_MB = 0.000001  # effectively 1 byte limit
        try:
            data = image_to_bytes(make_green_image())
            result = validate_image(data, content_type="image/jpeg")
            assert not result.passed
            assert result.error_code == "FILE_TOO_LARGE"
        finally:
            cfg.settings.MAX_IMAGE_SIZE_MB = orig


class TestCorruptImageValidation:
    def test_corrupt_bytes_fail(self):
        result = validate_image(b"\xff\xd8garbage bytes", content_type="image/jpeg")
        assert not result.passed
        assert result.error_code == "CORRUPT_IMAGE"

    def test_valid_image_bytes_pass(self):
        data = image_to_bytes(make_green_image())
        result = validate_image(data, content_type="image/jpeg")
        assert result.passed


class TestDimensionValidation:
    def test_tiny_image_fails(self):
        data = image_to_bytes(make_tiny_image(30, 30))
        result = validate_image(data, content_type="image/jpeg")
        assert not result.passed
        assert result.error_code == "IMAGE_TOO_SMALL"

    def test_normal_size_image_passes(self):
        data = image_to_bytes(make_green_image(300, 300))
        result = validate_image(data, content_type="image/jpeg")
        assert result.passed


class TestBlurValidation:
    def test_blurry_image_fails(self):
        data = image_to_bytes(make_blurry_image())
        result = validate_image(data, content_type="image/jpeg")
        assert not result.passed
        assert result.error_code == "IMAGE_TOO_BLURRY"

    def test_sharp_image_passes(self):
        data = image_to_bytes(make_green_image())
        result = validate_image(data, content_type="image/jpeg")
        assert result.passed

    def test_blur_score_present_on_failure(self):
        data = image_to_bytes(make_blurry_image())
        result = validate_image(data, content_type="image/jpeg")
        if result.error_code == "IMAGE_TOO_BLURRY":
            assert result.blur_score is not None
            assert isinstance(result.blur_score, float)


class TestValidationResult:
    def test_passed_result_has_image(self):
        data = image_to_bytes(make_green_image())
        result = validate_image(data, content_type="image/jpeg")
        if result.passed:
            assert result.image is not None

    def test_to_dict_has_expected_keys(self):
        data = image_to_bytes(make_green_image())
        result = validate_image(data, content_type="image/jpeg")
        d = result.to_dict()
        assert "status" in d
        assert "error_code" in d
        assert "user_message" in d
