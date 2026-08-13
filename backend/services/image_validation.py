"""Image quality validation gate for FieldMind.

Every uploaded image passes through this module before any ML inference runs.
The module is intentionally decoupled from FastAPI so it can be unit-tested
without an HTTP context.

Validation steps (in order):
    1. File type
    2. File size
    3. Corrupt / unreadable image
    4. Minimum dimensions
    5. Blur detection (Laplacian variance)

Each step returns a structured ``ValidationResult`` so callers can inspect
exactly what failed and present a user-friendly message.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np
from PIL import Image

from backend.core.config import settings

logger = logging.getLogger("fieldmind.validation")

# ── Result types ──────────────────────────────────────────────────────────────

ALLOWED_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/bmp",
        "image/tiff",
    }
)

ALLOWED_EXTENSIONS = frozenset(
    {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
)


class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"


@dataclass
class ValidationResult:
    """Result of image quality validation."""

    status: ValidationStatus
    """Overall pass/fail."""

    error_code: Optional[str] = None
    """Machine-readable code for the specific failure reason."""

    user_message: Optional[str] = None
    """Safe, user-friendly description of what went wrong."""

    details: dict = field(default_factory=dict)
    """Technical details (not exposed to end users)."""

    image: Optional[Image.Image] = None
    """The decoded PIL image — only present on success."""

    blur_score: Optional[float] = None
    """Laplacian variance score (higher = sharper)."""

    @property
    def passed(self) -> bool:
        return self.status == ValidationStatus.PASSED

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "error_code": self.error_code,
            "user_message": self.user_message,
            "details": self.details,
            "blur_score": self.blur_score,
        }


# ── Blur detection helper ─────────────────────────────────────────────────────


def _laplacian_variance(image: Image.Image) -> float:
    """Compute the variance of the Laplacian as a sharpness proxy.

    Uses a pure NumPy implementation to avoid a heavy OpenCV dependency.
    A higher value means sharper (less blurry) image.
    """
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    # 3×3 Laplacian kernel
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)

    # Manual 2-D convolution using stride tricks (avoids scipy dependency)
    h, w = gray.shape
    kh, kw = kernel.shape
    ph, pw = kh // 2, kw // 2

    padded = np.pad(gray, ((ph, ph), (pw, pw)), mode="reflect")
    output = np.zeros_like(gray)
    for i in range(kh):
        for j in range(kw):
            output += kernel[i, j] * padded[i : i + h, j : j + w]

    return float(np.var(output))


# ── Main validation function ──────────────────────────────────────────────────


def validate_image(
    image_bytes: bytes,
    content_type: Optional[str] = None,
    filename: Optional[str] = None,
) -> ValidationResult:
    """Run all image quality checks and return a ``ValidationResult``.

    Args:
        image_bytes:  Raw bytes of the uploaded file.
        content_type: MIME type reported by the HTTP client (may be absent).
        filename:     Original filename (used for extension check when
                      content_type is unreliable).

    Returns:
        A ``ValidationResult`` with ``passed=True`` and a decoded PIL image
        on success, or with ``passed=False`` and an error code on failure.
    """
    # ── 1. File type check ───────────────────────────────────────────────
    if content_type and not content_type.startswith("image/"):
        return ValidationResult(
            status=ValidationStatus.FAILED,
            error_code="INVALID_FILE_TYPE",
            user_message="Please upload a JPG, PNG, or WebP image of a plant leaf.",
            details={"content_type": content_type},
        )

    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        return ValidationResult(
            status=ValidationStatus.FAILED,
            error_code="UNSUPPORTED_IMAGE_FORMAT",
            user_message=(
                "Unsupported image format. Please upload a JPG, PNG, or WebP file."
            ),
            details={"content_type": content_type},
        )

    # ── 2. File size check ───────────────────────────────────────────────
    size_bytes = len(image_bytes)
    max_bytes = settings.max_image_size_bytes

    if size_bytes == 0:
        return ValidationResult(
            status=ValidationStatus.FAILED,
            error_code="EMPTY_FILE",
            user_message="The uploaded file is empty.",
            details={"size_bytes": 0},
        )

    if size_bytes > max_bytes:
        size_mb = size_bytes / (1024 * 1024)
        return ValidationResult(
            status=ValidationStatus.FAILED,
            error_code="FILE_TOO_LARGE",
            user_message=(
                f"Image is too large ({size_mb:.1f} MB). "
                f"Maximum allowed size is {settings.MAX_IMAGE_SIZE_MB:.0f} MB."
            ),
            details={"size_bytes": size_bytes, "max_bytes": max_bytes},
        )

    # ── 3. Corrupt image check ───────────────────────────────────────────
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()  # Force full decode — catches truncated files
    except Exception as exc:
        logger.debug("Image decode failed", extra={"error": str(exc)})
        return ValidationResult(
            status=ValidationStatus.FAILED,
            error_code="CORRUPT_IMAGE",
            user_message=(
                "The uploaded image could not be read. "
                "Please check the file is not corrupted."
            ),
            details={"error": str(exc)},
        )

    # ── 4. Dimension check ───────────────────────────────────────────────
    width, height = image.size
    min_dim = settings.MIN_IMAGE_DIMENSION_PX
    rec_min = settings.RECOMMENDED_MIN_IMAGE_DIMENSION_PX

    if width < min_dim or height < min_dim:
        return ValidationResult(
            status=ValidationStatus.FAILED,
            error_code="IMAGE_TOO_SMALL",
            user_message=(
                f"Image is too small ({width}×{height} px). "
                f"Please upload an image of at least {rec_min}×{rec_min} pixels."
            ),
            details={"width": width, "height": height, "min_dimension": min_dim},
        )

    # ── 5. Blur detection ────────────────────────────────────────────────
    blur_score = _laplacian_variance(image)
    blur_threshold = settings.IMAGE_BLUR_THRESHOLD

    if blur_score < blur_threshold:
        logger.info(
            "Image rejected: too blurry",
            extra={"blur_score": round(blur_score, 2), "threshold": blur_threshold},
        )
        return ValidationResult(
            status=ValidationStatus.FAILED,
            error_code="IMAGE_TOO_BLURRY",
            user_message=(
                "Image quality is insufficient for reliable diagnosis. "
                "Please upload a clearer image showing the affected leaf in good lighting."
            ),
            details={
                "blur_score": round(blur_score, 2),
                "blur_threshold": blur_threshold,
                "width": width,
                "height": height,
            },
            blur_score=round(blur_score, 2),
        )

    logger.debug(
        "Image validation passed",
        extra={
            "blur_score": round(blur_score, 2),
            "width": width,
            "height": height,
            "size_bytes": size_bytes,
        },
    )

    return ValidationResult(
        status=ValidationStatus.PASSED,
        image=image,
        blur_score=round(blur_score, 2),
        details={
            "width": width,
            "height": height,
            "size_bytes": size_bytes,
            "blur_score": round(blur_score, 2),
        },
    )
