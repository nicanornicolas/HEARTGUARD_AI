import json
from fastapi.testclient import TestClient
import sys
import os
import random
import pytest

# 1. PATH SETUP
# We need to tell Python where 'main.py' is located.
# This adds the parent directory (HeartGuard_AI) to the system path.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from main import app

# Initialize the Test Client
client = TestClient(app)

# TEST 1: System Health

def test_root_endpoint():
    """
    Checks if the API accepts requests.
    (Note: If you didn't define a root '/' in main.py, this might 404.
    We verify the docs endpoint or add a health check.)
    """
    response = client.get("/docs")
    assert response.status_code == 200


# TEST 2: The Happy Path (Normal Data)

def test_prediction_normal():
    """
    Sends 60 minutes of stable data (sleeping/sitting).
    Expects: Status 'Normal'
    """
    # Generate 60 mins of data: HR ~70, Activity=0
    payload = {
        "history": [
            {"heart_rate": 70.0, "activity_level": 0.0}
            for _ in range(60)
        ]
    }

    response = client.post("/analyze", json=payload)

    # Assertions
    assert response.status_code == 200
    json_data = response.json()

    assert "status" in json_data
    assert json_data['status'] == "Normal"
    # Ensure no massive deviation
    assert json_data["deviation"] < 10


# TEST 3: The Critical Anomaly (Heart Attack)

def test_prediction_critical():
    """
    Sends 59 minutes of normal data, then 1 minute of extreme spike while sitting,
    Expects: Status 'CRITICAL_aNOMALY'
    """
    # 59 mins of calm
    history = [
        {"heart_rate": 70.0, "activity_level": 0.0}
        for _ in range(59)
    ]

    # Minute 60: HR Spikes to 160, but Activity is still 0(Sitting)
    history.append({"heart_rate": 160.0, "activity_level": 0.0})

    payload = {"history": history}

    response = client.post("/analyze", json=payload)

    # Assertions
    assert response.status_code == 200
    json_data = response.json()

    print(f"\n[DEBUG] Critical Test Response: {json_data}")

    # The AI should predict ~70, Actual is 160. Diff ~90.
    assert json_data["status"] == "CRITICAL_ANOMALY"
    assert json_data["deviation"] > 20



# TEST 4: Input Validation (Bad Data)

def test_invalid_input_length():
    """
    Sends only 5 data points instead of 60.
    Expects: 400  Bad Request
    """
    payload = {
        "history": [
            {"heart_rate": 70.0, "activity_level": 0.0}
            for _ in range(5)
        ]
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 400