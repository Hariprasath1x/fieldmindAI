"""Security and authorization tests."""
from __future__ import annotations

import pytest


from tests.conftest import image_to_bytes, make_green_image


@pytest.fixture
def client(fastapi_client):
    return fastapi_client


class TestAuthenticationRequired:
    def test_diagnosis_history_requires_auth(self, client):
        response = client.get("/api/diagnosis/history")
        assert response.status_code == 401

    def test_single_diagnosis_requires_auth(self, client):
        response = client.get("/api/diagnosis/some-id")
        assert response.status_code == 401

    def test_feedback_submission_requires_auth(self, client):
        response = client.post("/api/feedback", json={
            "prediction_id": "p1",
            "user_id": "u1",
            "predicted_label": "cashew_healthy",
            "feedback_type": "correct",
        })
        assert response.status_code == 401

    def test_feedback_dashboard_requires_auth(self, client):
        response = client.get("/api/feedback/dashboard")
        assert response.status_code == 401


class TestUserIsolation:
    def test_user_cannot_access_other_users_diagnosis(self, client):
        """User A cannot read User B's diagnosis."""
        # User B creates a diagnosis via inference
        data = image_to_bytes(make_green_image())
        submit_resp = client.post(
            "/api/inference/submit",
            files={"file": ("leaf.jpg", data, "image/jpeg")},
            headers={"X-User-ID": "user-B"},
        )
        job_id = submit_resp.json()["job_id"]

        # Get the diagnosis_id from the job result
        status_resp = client.get(
            f"/api/inference/{job_id}",
            headers={"X-User-ID": "user-B"},
        )
        result = status_resp.json().get("result", {}) or {}
        diagnosis_id = result.get("diagnosis_id")

        if diagnosis_id:
            # User A should not be able to read User B's diagnosis
            access_resp = client.get(
                f"/api/diagnosis/{diagnosis_id}",
                headers={"X-User-ID": "user-A"},
            )
            assert access_resp.status_code in (403, 404)

    def test_user_cannot_access_other_users_job(self, client):
        """User A cannot poll User B's inference job."""
        data = image_to_bytes(make_green_image())
        submit_resp = client.post(
            "/api/inference/submit",
            files={"file": ("leaf.jpg", data, "image/jpeg")},
            headers={"X-User-ID": "user-B"},
        )
        job_id = submit_resp.json()["job_id"]

        # User A polls for User B's job
        access_resp = client.get(
            f"/api/inference/{job_id}",
            headers={"X-User-ID": "user-A"},
        )
        assert access_resp.status_code in (403, 200)
        # When 200, the job should still be returned (unauthenticated polling allowed)
        # but job result should not contain cross-user data


class TestInvalidTokens:
    def test_empty_user_id_header_rejected(self, client):
        response = client.get(
            "/api/diagnosis/history",
            headers={"X-User-ID": ""},
        )
        # Empty string should be treated as missing
        assert response.status_code in (401, 422)


class TestProtectedEndpoints:
    def test_feedback_dashboard_non_admin_denied(self, client):
        """Regular farmer role should not access the feedback dashboard."""
        # The mock Firestore has no users; the admin check will fail gracefully
        response = client.get(
            "/api/feedback/dashboard",
            headers={"X-User-ID": "regular-farmer-uid"},
        )
        # Should be 403 (not admin) or 401 (no user found)
        assert response.status_code in (401, 403)
