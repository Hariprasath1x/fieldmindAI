import requests

url = "http://localhost:8003/api/marketplace/users/sync"
payload = {
    "uid": "test_uid_123",
    "email": "test@example.com",
    "displayName": "Test User",
    "phone": "+919876543210",
    "role": "Farmer",
    "language": "en"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
