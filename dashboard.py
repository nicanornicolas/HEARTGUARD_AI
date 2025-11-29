import streamlit as st
import requests 
import pandas as pd
import numpy as np
import time


# CONFIG
API_URL = "http://127.0.0.1:8000/analyze"
st.set_page_config(page_title="HeartGuard AI Monitor", layout="wide")

st.title("🫀 HeartGuard AI: Real-Time Telemetry")

# 1. SESSION STATE (To store history across re-runs)
# Steamlit re-runs the script on every interaction. We need to remember data.
if "data_history" not in st.session_state:
    # Initialize with 60 minutes of "Normal" data
    # Structure: [[HR, Activity], [HR, Activity]...]
    initial_data = []
    for _ in range(60):
        initial_data.append({"heart_rate": 70, "activity_level": 0})
    st.session_state["data_history"] = initial_data


# 2. SIDEBAR CONTROLS (Simulating the Wearable Device)
st.sidebar.header("Wearable Simulator")
st.sidebar.markdown("Adjust current user state:")

# Sliders to simulate what the watch is seeing NOW
current_hr = st.sidebar.slider("Current Heart Rate (BPM)", 40, 200, 70)
current_activity = st.sidebar.selectbox("Current Activity", [0, 1, 2],
format_func=lambda x: ["Sitting", "Walking", "Running"][x])

# 3. MAIN LOGIC
# Add the new reading to history
new_reading = {"heart_rate": current_hr, "activity_level": current_activity}

# Update Session State: Remove oldest, add newest
st.session_state["data_history"].pop(0)
st.session_state["data_history"].append(new_reading)

# 4. CALL THE API
# We send the update history to the " Brain"
payload = {"history": st.session_state["data_history"]}


try:
    response = requests.post(API_URL, json=payload)
    if response.status_code == 200:
        result = response.json()


        # 5. VISUALIZATION
        col1, col2, col3 = st.columns(3)

        # Metric 1: Prediction
        col1.metric("AI Predicted HR", f"{result['predicted_safe_bpm']} BPM")

        # Metric 2: Actual
        col2.metric("Actual HR", f"{current_hr} BPM",
        delta=round(current_hr - result['predicted_safe_bpm'], 1))

        # Metric 3: Status
        status = result['status']
        if status == "CRITICAL_ANOMALY":
            col3.error("⚠️ CRITICAL ANOMALY DETECTED")
        elif status == "WARNING":
            col3.warning("High Deviation")
        else:
            col3.success("Normal Rhythm")

    else:
        st.error(f"API Error: {response.text}")

except Exception as e:
    st.error(f"Connection Failed. Is main.py running? {e}")


# 6. CHARTING
# Convert history to DataFrame for plotting
df = pd.DataFrame(st.session_state["data_history"])
st.line_chart(df["heart_rate"])

st.markdown("---")
st.caption("Auto-refreshing is manial in this demo mode. In production, we use st.empty() loops.")