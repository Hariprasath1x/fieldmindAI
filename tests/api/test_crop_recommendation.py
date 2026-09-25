import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from backend.main import app

# Create a mock for the crop_model.
mock_crop_model = MagicMock()
mock_crop_model.classes_ = np.array(["rice", "apple", "mothbeans", "pigeonpeas", "jute"])

def mock_predict_proba(features):
    # Depending on input features (just dummy values for now), return predictable probs.
    # We will just return a static array for testing.
    return np.array([[0.10, 0.50, 0.12, 0.13, 0.15]])

mock_crop_model.predict_proba = mock_predict_proba

@pytest.fixture
def override_crop_model():
    with patch("backend.main.inference_service.crop_model", mock_crop_model), \
         patch("backend.main.inference_service.is_ready", True):
        yield

def test_crop_recommendation_tamil_nadu(fastapi_client, override_crop_model):
    # Test case: Tamil Nadu + Mothbeans & Pigeonpeas & Apple
    payload = {
        "N": 50,
        "P": 50,
        "K": 50,
        "temperature": 25,
        "humidity": 60,
        "pH": 6.5,
        "rainfall": 100,
        "state": "Tamil Nadu",
        "country": "India"
    }
    
    response = fastapi_client.post("/predict/crop", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Let's print the results to stdout so we can see them in the test log
    print("TAMIL NADU RESULTS:")
    for i, r in enumerate(data.get("recommendations", [])):
        print(f"Alt {i}: {r['crop']} - Conf: {r['confidence']} - Regional: {r.get('regional_info')}")
    
def test_crop_recommendation_no_region(fastapi_client, override_crop_model):
    payload = {
        "N": 50,
        "P": 50,
        "K": 50,
        "temperature": 25,
        "humidity": 60,
        "pH": 6.5,
        "rainfall": 100
    }
    response = fastapi_client.post("/predict/crop", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    print("NO REGION RESULTS:")
    for i, r in enumerate(data.get("recommendations", [])):
        print(f"Alt {i}: {r['crop']} - Conf: {r['confidence']} - Regional: {r.get('regional_info')}")

