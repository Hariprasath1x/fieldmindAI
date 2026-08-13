"""API tests for marketplace endpoints."""
from __future__ import annotations

import pytest



@pytest.fixture
def client(fastapi_client):
    return fastapi_client


class TestEquipmentEndpoints:
    def test_get_all_equipment_returns_200(self, client):
        response = client.get("/api/marketplace/equipment")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_equipment_returns_201_or_200(self, client):
        payload = {
            "name": "Tractor",
            "category": "Heavy",
            "hourlyPrice": 100.0,
            "dailyPrice": 700.0,
            "location": "Chennai",
            "village": "Ponneri",
            "quantity": 1,
            "ownerId": "owner-001",
            "ownerName": "Ravi",
            "ownerPhone": "9999999999",
        }
        response = client.post("/api/marketplace/equipment", json=payload)
        assert response.status_code in (200, 201)
        body = response.json()
        assert "id" in body
        assert body["name"] == "Tractor"

    def test_delete_equipment(self, client):
        # Create first
        payload = {
            "name": "Plough",
            "category": "Manual",
            "hourlyPrice": 10.0,
            "dailyPrice": 70.0,
            "location": "Chennai",
            "village": "Ponneri",
            "quantity": 2,
            "ownerId": "owner-001",
            "ownerName": "Ravi",
            "ownerPhone": "9999999999",
        }
        create_resp = client.post("/api/marketplace/equipment", json=payload)
        item_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/api/marketplace/equipment/{item_id}")
        assert delete_resp.status_code == 200


class TestWorkerEndpoints:
    def test_get_all_workers_returns_list(self, client):
        response = client.get("/api/marketplace/workers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_worker(self, client):
        payload = {
            "name": "Kumar",
            "phone": "8888888888",
            "village": "Kanchipuram",
            "experience": "5 years",
            "skills": ["Ploughing", "Irrigation"],
            "dailyWage": 500.0,
            "hourlyWage": 60.0,
            "availableDays": ["Monday", "Tuesday"],
            "availableTime": "06:00-18:00",
            "languages": ["Tamil"],
            "managerId": "mgr-001",
        }
        response = client.post("/api/marketplace/workers", json=payload)
        assert response.status_code in (200, 201)
        assert response.json()["name"] == "Kumar"


class TestBookingLifecycle:
    def _create_equipment(self, client) -> str:
        payload = {
            "name": "Harvester",
            "category": "Heavy",
            "hourlyPrice": 200.0,
            "dailyPrice": 1200.0,
            "location": "Coimbatore",
            "village": "Palladam",
            "quantity": 1,
            "ownerId": "owner-101",
            "ownerName": "Selva",
            "ownerPhone": "7777777777",
        }
        r = client.post("/api/marketplace/equipment", json=payload)
        return r.json()["id"]

    def test_full_booking_lifecycle_approved(self, client):
        eq_id = self._create_equipment(client)

        # Create booking
        booking_payload = {
            "type": "Equipment",
            "targetId": eq_id,
            "targetName": "Harvester",
            "requesterId": "farmer-001",
            "ownerId": "owner-101",
            "date": "2026-09-01",
            "timeSlot": "08:00",
            "duration": "4 hours",
        }
        create_resp = client.post("/api/marketplace/bookings", json=booking_payload)
        assert create_resp.status_code in (200, 201)
        booking = create_resp.json()
        booking_id = booking["id"]
        assert booking["status"] == "Pending"

        # Approve
        approve_resp = client.put(
            f"/api/marketplace/bookings/{booking_id}/status?status=Approved"
        )
        assert approve_resp.status_code == 200

        # Complete
        complete_resp = client.put(
            f"/api/marketplace/bookings/{booking_id}/status?status=Completed"
        )
        assert complete_resp.status_code == 200

    def test_booking_lifecycle_rejected(self, client):
        eq_id = self._create_equipment(client)
        booking_payload = {
            "type": "Equipment",
            "targetId": eq_id,
            "targetName": "Harvester",
            "requesterId": "farmer-002",
            "ownerId": "owner-101",
            "date": "2026-09-02",
            "timeSlot": "10:00",
            "duration": "2 hours",
        }
        create_resp = client.post("/api/marketplace/bookings", json=booking_payload)
        booking_id = create_resp.json()["id"]

        reject_resp = client.put(
            f"/api/marketplace/bookings/{booking_id}/status?status=Rejected"
        )
        assert reject_resp.status_code == 200

    def test_invalid_booking_status_rejected(self, client):
        eq_id = self._create_equipment(client)
        booking_payload = {
            "type": "Equipment",
            "targetId": eq_id,
            "targetName": "Harvester",
            "requesterId": "farmer-003",
            "ownerId": "owner-101",
            "date": "2026-09-03",
            "timeSlot": "14:00",
            "duration": "1 hour",
        }
        create_resp = client.post("/api/marketplace/bookings", json=booking_payload)
        booking_id = create_resp.json()["id"]

        invalid_resp = client.put(
            f"/api/marketplace/bookings/{booking_id}/status?status=InvalidStatus"
        )
        assert invalid_resp.status_code == 400

    def test_farmer_bookings(self, client):
        response = client.get("/api/marketplace/bookings/farmer/farmer-001")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_owner_bookings(self, client):
        response = client.get("/api/marketplace/bookings/owner/owner-101")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
