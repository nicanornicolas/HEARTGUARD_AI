from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
import torch.nn as nn
import joblib
import numpy as np
from typing import List
import os

# Robust path handling
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "artifacts")

# Define Model Class (exactly matches the training)
class HealthLSTM(nn.Module):
    def __init__(self, input_size=2, hidden_size=50, output_size=1):
        super(HealthLSTM, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])  # Predict only the last time step


app = FastAPI()

# Load Artifacts
model = HealthLSTM(input_size=2)
model.load_state_dict(torch.load(os.path.join(ARTIFACTS_DIR, 'health_model_v2.pth')))
model.eval()
scaler = joblib.load(os.path.join(ARTIFACTS_DIR,'health_scaler.pk1'))

class HealthRecord(BaseModel):
    heart_rate: float
    activity_level: float # 0=Sit, 1=Walk, 2=Run


class PatientData(BaseModel):
    history: List[HealthRecord] # Requires last 60mins

@app.post("/analyze")
async def analyze_health(data: PatientData):
    if len(data.history) != 60:
        raise HTTPException(status_code=400, detail="Requires exactly 60 minutes of data")
    

    # 1. Preprocess
    raw = [[d.heart_rate, d.activity_level] for d in data.history]
    scaled = scaler.transform(np.array(raw))
    tensor_in = torch.tensor(scaled, dtype=torch.float32).unsqueeze(0) # Add batch dimension

    # 2. Predict
    with torch.no_grad():
        pred_scaled = model(tensor_in).item()

    # 3. Inverse Transform(Trick: Create dummy array for scaler)
    dummy = np.array([[pred_scaled, 0]])
    pred_bpm = scaler.inverse_transform(dummy)[0][0]

    # 4. Logic
    actual_bpm = raw[-1][0]
    diff = abs(actual_bpm - pred_bpm)

    status = "Normal"
    if diff > 20: status = "CRITICAL_ANOMALY"
    elif diff > 10: status = "WARNING"

    return {
        "status": status,
        "actual_bpm": actual_bpm,
        "predicted_safe_bpm": round(pred_bpm,1),
        "deviation": round(diff, 1)
    }