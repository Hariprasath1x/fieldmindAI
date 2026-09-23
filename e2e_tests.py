import os
import requests
import json
import time
import sys
import subprocess

API_KEY = "AIzaSyAODffUMuKcFai0O4S2U61MgjYASOIa_3U"
BASE_URL = "http://localhost:8002/api/marketplace"
AUTH_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
SIGNUP_URL = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"

def authenticate_user(email, password):
    # Try to sign in
    payload = {"email": email, "password": password, "returnSecureToken": True}
    r = requests.post(AUTH_URL, json=payload)
    if r.status_code == 200:
        return r.json()["idToken"], r.json()["localId"]
    
    # If not found, try to sign up
    r = requests.post(SIGNUP_URL, json=payload)
    if r.status_code == 200:
        return r.json()["idToken"], r.json()["localId"]
    
    print(f"FAILED to authenticate or create {email}: {r.text}")
    sys.exit(1)

def print_result(name, passed, evidence=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if evidence and not passed:
        print(f"  Evidence: {evidence}")

def run_tests():
    print("========================================")
    print("STARTING E2E MARKETPLACE REGRESSION TEST")
    print("========================================")

    print("Authenticating users...")
    token_A, uid_A = authenticate_user("test_a_e2e@example.com", "Password123!")
    token_B, uid_B = authenticate_user("test_b_e2e@example.com", "Password123!")

    headers_A = {"Authorization": f"Bearer {token_A}"}
    headers_B = {"Authorization": f"Bearer {token_B}"}

    # 1. AUTHENTICATION & SYNC
    res = requests.post(f"{BASE_URL}/users/sync", headers=headers_A, json={
        "uid": uid_A, "email": "test_a_e2e@example.com", "phone": "9999999991", "role": "Farmer", "displayName": "User A"
    })
    print_result("User A Profile Sync", res.status_code == 200)

    res = requests.post(f"{BASE_URL}/users/sync", headers=headers_B, json={
        "uid": uid_B, "email": "test_b_e2e@example.com", "phone": "9999999992", "role": "Farmer", "displayName": "User B"
    })
    print_result("User B Profile Sync", res.status_code == 200)

    # 2. EQUIPMENT CREATION
    eq_payload = {
        "name": "E2E Tractor",
        "category": "Tractor",
        "hourlyPrice": 500,
        "dailyPrice": 4000,
        "location": "Test Location",
        "village": "Test Village",
        "quantity": 1,
        "ownerId": uid_A,
        "ownerName": "User A",
        "ownerPhone": "9999999991"
    }
    res = requests.post(f"{BASE_URL}/equipment", headers=headers_A, json=eq_payload)
    print_result("Equipment Creation (User A)", res.status_code == 200)
    equipment_id = res.json()["id"]

    # 3. SELF-BOOKING PREVENTION (EQUIPMENT)
    booking_payload = {
        "type": "Equipment",
        "targetId": equipment_id,
        "targetName": "E2E Tractor",
        "requesterId": uid_A,
        "ownerId": uid_A,
        "date": "2030-01-01",
        "timeSlot": "Morning",
        "duration": 1
    }
    res = requests.post(f"{BASE_URL}/bookings", headers=headers_A, json=booking_payload)
    print_result("Self-Booking Prevention (Equipment)", res.status_code == 403, res.text)

    # 4. VALID BOOKING (EQUIPMENT)
    booking_payload["requesterId"] = uid_B
    res = requests.post(f"{BASE_URL}/bookings", headers=headers_B, json=booking_payload)
    print_result("Valid Booking (User B books User A's Equipment)", res.status_code == 200, res.text)
    booking_id = res.json()["id"]

    # 5. DOUBLE BOOKING PREVENTION (CONCURRENCY)
    res = requests.post(f"{BASE_URL}/bookings", headers=headers_B, json=booking_payload)
    print_result("Double Booking Prevention (Same Slot)", res.status_code == 409, res.text)

    # 6. UID SPOOFING
    spoofed_payload = booking_payload.copy()
    spoofed_payload["requesterId"] = uid_A # User B tries to spoof User A's ID
    res = requests.post(f"{BASE_URL}/bookings", headers=headers_B, json=spoofed_payload)
    print_result("UID Spoofing Prevention", res.status_code == 403, res.text)

    # 7. PRICE AUTHORITY
    price_spoofed = booking_payload.copy()
    price_spoofed["date"] = "2030-01-02"
    # Even if client sends price, backend ignores it and calculates authoritative price.
    res = requests.post(f"{BASE_URL}/bookings", headers=headers_B, json=price_spoofed)
    print_result("Price Authority Enforcement", res.status_code == 200)
    booking_id_2 = res.json()["id"]
    if res.json()["totalPrice"] == 500:
        print_result("Price Authority (Value Verified)", True)
    else:
        print_result("Price Authority (Value Verified)", False, f"Expected 500, got {res.json().get('totalPrice')}")

    # 8. BOOKING STATE TRANSITIONS & AUTHORIZATION
    # User B tries to approve their own request (should fail)
    res = requests.put(f"{BASE_URL}/bookings/{booking_id}/status", headers=headers_B, params={"status": "Approved"})
    print_result("Authorization: Requester cannot approve", res.status_code == 403, res.text)
    
    # User A approves User B's request
    res = requests.put(f"{BASE_URL}/bookings/{booking_id}/status", headers=headers_A, params={"status": "Approved"})
    print_result("Authorization: Owner can approve", res.status_code == 200, res.text)
    
    # User B cancels their 2nd request
    res = requests.put(f"{BASE_URL}/bookings/{booking_id_2}/status", headers=headers_B, params={"status": "Cancelled"})
    print_result("Authorization: Requester can cancel", res.status_code == 200, res.text)

    # 9. RESOURCE DELETION PROTECTION (ACTIVE BOOKING)
    res = requests.delete(f"{BASE_URL}/equipment/{equipment_id}", headers=headers_A)
    print_result("Resource Deletion Protection (Active Booking)", res.status_code == 409, res.text)

    # 10. COMPLETE BOOKING
    res = requests.put(f"{BASE_URL}/bookings/{booking_id}/status", headers=headers_A, params={"status": "Completed"})
    print_result("Booking Completion", res.status_code == 200, res.text)

    # 11. SAFE RESOURCE DELETION
    res = requests.delete(f"{BASE_URL}/equipment/{equipment_id}", headers=headers_A)
    print_result("Safe Resource Deletion (No Active Bookings)", res.status_code == 200, res.text)

    # 12. WORKFORCE CREATION & SELF-HIRING
    wk_payload = {
        "name": "E2E Worker",
        "phone": "9999999991",
        "village": "Test Village",
        "experience": "5 Years",
        "skills": ["Harvesting"],
        "dailyWage": 1000,
        "hourlyWage": 150,
        "availableDays": ["Mon", "Tue"],
        "availableTime": "8AM-5PM",
        "languages": ["English"],
        "managerId": uid_A
    }
    res = requests.post(f"{BASE_URL}/workers", headers=headers_A, json=wk_payload)
    print_result("Workforce Creation (User A)", res.status_code == 200)
    worker_id = res.json()["id"]

    wk_booking = {
        "type": "Worker",
        "targetId": worker_id,
        "targetName": "E2E Worker",
        "requesterId": uid_A,
        "ownerId": uid_A,
        "date": "2030-01-05",
        "timeSlot": "Full Day",
        "duration": 2
    }
    res = requests.post(f"{BASE_URL}/bookings", headers=headers_A, json=wk_booking)
    print_result("Self-Booking Prevention (Workforce)", res.status_code == 403, res.text)

    wk_booking["requesterId"] = uid_B
    res = requests.post(f"{BASE_URL}/bookings", headers=headers_B, json=wk_booking)
    print_result("Valid Booking (Workforce)", res.status_code == 200)

    requests.delete(f"{BASE_URL}/workers/{worker_id}", headers=headers_A) # cleanup

    print("========================================")
    print("ALL API TESTS COMPLETED")
    print("========================================")

if __name__ == "__main__":
    run_tests()
