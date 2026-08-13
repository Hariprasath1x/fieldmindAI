"""API tests for health and readiness endpoints."""
from __future__ import annotations

import pytest



@pytest.fixture
def client(fastapi_client):
    return fastapi_client


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_body(self, client):
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert "service" in data

    def test_health_is_fast(self, client):
        import time
        t = time.perf_counter()
        client.get("/health")
        elapsed = (time.perf_counter() - t) * 1000
        assert elapsed < 500, f"Health check took {elapsed:.0f}ms (should be < 500ms)"


class TestReadinessEndpoint:
    def test_ready_returns_response(self, client):
        response = client.get("/ready")
        # May be 200 or 503 depending on state
        assert response.status_code in (200, 503)

    def test_ready_has_checks(self, client):
        data = client.get("/ready").json()
        assert "checks" in data
        assert "status" in data

    def test_ready_checks_include_ml_models(self, client):
        data = client.get("/ready").json()
        # ml_models check should be present
        assert "ml_models" in data["checks"]


class TestMetricsEndpoint:
    def test_metrics_returns_200(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_has_expected_keys(self, client):
        data = client.get("/metrics").json()
        assert "api_requests_total" in data
        assert "inference_requests_total" in data

    def test_metrics_values_are_non_negative(self, client):
        data = client.get("/metrics").json()
        for key, val in data.items():
            if isinstance(val, (int, float)) and val is not None:
                assert val >= 0, f"{key} should be non-negative"


class TestRootEndpoint:
    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_has_message(self, client):
        data = client.get("/").json()
        assert "message" in data
