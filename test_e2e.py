import requests
import json
import firebase_admin
from firebase_admin import credentials, auth
import sys

API_KEY = "AIzaSyAODffUMuKcFai0O4S2U61MgjYASOIa_3U"

def get_id_token(uid):
    # Initialize firebase admin if not already
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_service_account.json")
        firebase_admin.initialize_app(cred)
    
    # Mint a custom token
    custom_token = auth.create_custom_token(uid)
    
    # Exchange for ID token
    data = {
        "token": custom_token.decode("utf-8"),
        "returnSecureToken": True
    }
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={API_KEY}"
    response = requests.post(url, json=data)
    response.raise_for_status()
    return response.json()["idToken"]

def test_flow():
    base_url = "http://localhost:8002"
    uid = "test-e2e-user-123"
    print(f"Testing flow for UID: {uid}")
    
    id_token = get_id_token(uid)
    headers = {"Authorization": f"Bearer {id_token}"}
    
    # 1. User Sync
    print("1. Testing User Sync...")
    sync_data = {
        "uid": uid,
        "displayName": "Test User",
        "email": "test@example.com",
        "role": "Farmer",
        "language": "en"
    }
    r = requests.post(f"{base_url}/api/marketplace/users/sync", json=sync_data, headers=headers)
    print("Sync response:", r.status_code, r.text)
    r.raise_for_status()
    
    # 2. Equipment Creation
    print("2. Testing Equipment Creation...")
    eq_data = {
        "name": "Test Tractor",
        "category": "Tractor",
        "hourlyPrice": 500.0,
        "dailyPrice": 4000.0,
        "location": "Test City",
        "village": "Test Village",
        "quantity": 2,
        "isAvailable": True,
        "description": "A test tractor",
        "ownerId": uid,
        "ownerName": "Test User",
        "ownerPhone": "1234567890"
    }
    r = requests.post(f"{base_url}/api/marketplace/equipment", json=eq_data, headers=headers)
    print("Equipment create response:", r.status_code, r.text)
    r.raise_for_status()
    eq_id = r.json()["id"]
    
    # 3. Workforce Creation
    print("3. Testing Worker Creation...")
    worker_data = {
        "name": "Test Worker",
        "phone": "0987654321",
        "village": "Test Village",
        "experience": "5 Years",
        "skills": ["Driving", "Harvesting"],
        "dailyWage": 800.0,
        "hourlyWage": 100.0,
        "availableDays": ["Mon", "Tue"],
        "availableTime": "8am - 5pm",
        "languages": ["Tamil"],
        "managerId": uid
    }
    r = requests.post(f"{base_url}/api/marketplace/workers", json=worker_data, headers=headers)
    print("Worker create response:", r.status_code, r.text)
    r.raise_for_status()
    worker_id = r.json()["id"]
    
    # 4. Booking Creation (Success)
    print("4. Testing Booking Creation...")
    booking_data = {
        "targetId": eq_id,
        "targetName": "Test Tractor",
        "type": "Equipment",
        "date": "2030-10-10",
        "timeSlot": "Morning",
        "duration": 4,
        "requesterId": uid,
        "requesterName": "Test User",
        "requesterPhone": "1234567890",
        "ownerId": uid
    }
    r = requests.post(f"{base_url}/api/marketplace/bookings", json=booking_data, headers=headers)
    print("Booking response:", r.status_code, r.text)
    if r.status_code != 200:
        print("FAIL: First booking should succeed. Check if index error occurred!")
        sys.exit(1)
    
    booking_id = r.json()["id"]
    
    # 5. Booking Creation (Double Booking - Expect 409)
    print("5. Testing Booking Concurrency (Double Booking)...")
    r2 = requests.post(f"{base_url}/api/marketplace/bookings", json=booking_data, headers=headers)
    print("Double Booking response:", r2.status_code, r2.text)
    if r2.status_code != 409:
        print(f"FAIL: Expected 409 Conflict, got {r2.status_code}")
        sys.exit(1)
        
    print("All tests PASSED.")

if __name__ == "__main__":
    test_flow()
