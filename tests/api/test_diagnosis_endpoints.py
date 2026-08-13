"""API tests for diagnosis and inference endpoints."""
from __future__ import annotations

import pytest

from tests.conftest import image_to_bytes, make_blurry_image, make_green_image


@pytest.fixture
def client(fastapi_client):
    return fastapi_client


class TestInferenceSubmit:
    def test_submit_valid_image_returns_job_id(self, client):
        data = image_to_bytes(make_green_image())
        response = client.post(
            "/api/inference/submit",
            files={"file": ("leaf.jpg", data, "image/jpeg")},
        )
        assert response.status_code == 200
        body = response.json()
        assert "job_id" in body
        assert body["job_id"]

    def test_submit_returns_status(self, client):
        data = image_to_bytes(make_green_image())
        response = client.post(
            "/api/inference/submit",
            files={"file": ("leaf.jpg", data, "image/jpeg")},
        )
        body = response.json()
        assert body["status"] in ("queued", "completed", "processing", "failed")

    def test_submit_non_image_fails(self, client):
        response = client.post(
            "/api/inference/submit",
            files={"file": ("doc.pdf", b"fake pdf", "application/pdf")},
        )
        assert response.status_code == 400

    def test_submit_empty_file_fails(self, client):
        response = client.post(
            "/api/inference/submit",
            files={"file": ("empty.jpg", b"", "image/jpeg")},
        )
        assert response.status_code == 400

    def test_submit_blurry_image_returns_completed(self, client):
        """Blurry images complete the job (validation fails gracefully)."""
        data = image_to_bytes(make_blurry_image())
        response = client.post(
            "/api/inference/submit",
            files={"file": ("blurry.jpg", data, "image/jpeg")},
        )
        assert response.status_code == 200


class TestInferenceStatus:
    def test_status_for_valid_job(self, client):
        # Submit first
        data = image_to_bytes(make_green_image())
        submit_resp = client.post(
            "/api/inference/submit",
            files={"file": ("leaf.jpg", data, "image/jpeg")},
        )
        job_id = submit_resp.json()["job_id"]

        # Poll status
        status_resp = client.get(f"/api/inference/{job_id}")
        assert status_resp.status_code == 200
        body = status_resp.json()
        assert body["job_id"] == job_id
        assert "status" in body
        assert "created_at" in body

    def test_status_for_unknown_job_returns_404(self, client):
        response = client.get("/api/inference/nonexistent-job-id-12345")
        assert response.status_code == 404


class TestDiagnosisHistory:
    def test_history_requires_auth(self, client):
        response = client.get("/api/diagnosis/history")
        assert response.status_code == 401

    def test_history_with_user_id_header(self, client):
        response = client.get(
            "/api/diagnosis/history",
            headers={"X-User-ID": "test-user-123"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "diagnoses" in body
        assert "total" in body

    def test_history_respects_limit(self, client):
        response = client.get(
            "/api/diagnosis/history?limit=5",
            headers={"X-User-ID": "test-user-123"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total"] <= 5


class TestDiagnosisGet:
    def test_get_nonexistent_diagnosis_404(self, client):
        response = client.get(
            "/api/diagnosis/nonexistent-id",
            headers={"X-User-ID": "user-1"},
        )
        assert response.status_code == 404

    def test_get_diagnosis_requires_auth(self, client):
        response = client.get("/api/diagnosis/some-id")
        assert response.status_code == 401


class TestLegacyDiseaseEndpoint:
    def test_legacy_endpoint_with_valid_image(self, client):
        data = image_to_bytes(make_green_image())
        response = client.post(
            "/predict/disease",
            files={"file": ("leaf.jpg", data, "image/jpeg")},
        )
        assert response.status_code == 200
        body = response.json()
        assert "success" in body

    def test_legacy_endpoint_rejects_non_image(self, client):
        response = client.post(
            "/predict/disease",
            files={"file": ("doc.txt", b"text content", "text/plain")},
        )
        assert response.status_code == 400
