import streamlit as st
import websocket
import json
import pandas as pd
import time
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import deque
import os

# App config
st.set_page_config(
    page_title="Live Telemetry Dashboard", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)
st.title("🛰️ Real-Time Telemetry & Anomaly Detection")

# Initialize session state for rolling data windows
if "telemetry_data" not in st.session_state:
    st.session_state.telemetry_data = deque(maxlen=200) 
if "alert_logs" not in st.session_state:
    st.session_state.alert_logs = deque(maxlen=50)

# Fetch backend URL from environment or use default
backend_host = os.environ.get("BACKEND_HOST", "localhost")
WS_URL = f"ws://{backend_host}:8000/ws/telemetry"

st.sidebar.header("Connection Settings")
st.sidebar.text(f"URL: {WS_URL}")
if st.sidebar.button("Reconnect"):
    st.rerun()

# Layout Placeholders for real-time updates
kpi_container = st.empty()
chart_container = st.empty()
st.subheader("⚠️ Recent Anomaly Alerts")
log_container = st.empty()

try:
    ws = websocket.create_connection(WS_URL, timeout=2)
    st.sidebar.success("Connected to Backend")
    connected = True
except Exception as e:
    st.sidebar.error("Disconnected")
    st.error(f"Could not connect to FastAPI backend at {WS_URL}. Make sure it is running.")
    connected = False

if connected:
    while True:
        try:
            # Receive string data from WebSocket
            data = ws.recv()
            payload = json.loads(data)
            
            # Parse components
            ts = pd.to_datetime(payload["timestamp"])
            metrics = payload["metrics"]
            analysis = payload["analysis"]
            
            # Append to rolling data store
            st.session_state.telemetry_data.append({
                "timestamp": ts,
                "voltage": metrics.get("voltage"),
                "temperature": metrics.get("temperature"),
                "vibration_rms": metrics.get("vibration_rms"),
                "anomaly_score": analysis.get("anomaly_score"),
                "status": analysis.get("status")
            })
            
            # If anomaly detected, push to alert log
            if analysis.get("is_anomaly"):
                st.session_state.alert_logs.append({
                    "Timestamp": ts.strftime('%H:%M:%S.%f')[:-3],
                    "Severity": analysis.get("status"),
                    "Score": analysis.get("anomaly_score"),
                    "Voltage (V)": f"{metrics.get('voltage'):.2f}",
                    "Temp (°C)": f"{metrics.get('temperature'):.2f}",
                    "Vib (RMS)": f"{metrics.get('vibration_rms'):.3f}"
                })
            
            df = pd.DataFrame(st.session_state.telemetry_data)
            latest = df.iloc[-1]
            
            # --- Render KPIs ---
            with kpi_container.container():
                cols = st.columns(5)
                status_color = "🟢" if latest["status"] == "NOMINAL" else ("🟠" if latest["status"] == "WARNING" else "🔴")
                cols[0].metric("System Status", f"{status_color} {latest['status']}")
                cols[1].metric("Temperature (°C)", f"{latest['temperature']:.2f}")
                cols[2].metric("Voltage (V)", f"{latest['voltage']:.2f}")
                cols[3].metric("Vibration (RMS)", f"{latest['vibration_rms']:.3f}")
                cols[4].metric("Anomaly Score", f"{latest['anomaly_score']:.2f}")

            # --- Render Rolling Charts ---
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05)
            
            fig.add_trace(go.Scatter(x=df["timestamp"], y=df["temperature"], name="Temp (°C)", line=dict(color="#ff9900")), row=1, col=1)
            fig.add_trace(go.Scatter(x=df["timestamp"], y=df["voltage"], name="Voltage (V)", line=dict(color="#3399ff")), row=2, col=1)
            fig.add_trace(go.Scatter(x=df["timestamp"], y=df["anomaly_score"], name="Anomaly Score", fill='tozeroy', line=dict(color="#ff3333")), row=3, col=1)
            
            # Draw threshold lines
            fig.add_hline(y=0.15, line_dash="dash", line_color="red", row=3, col=1, annotation_text="Critical Threshold")
            
            fig.update_layout(height=600, margin=dict(l=0, r=0, t=30, b=0), template="plotly_dark")
            chart_container.plotly_chart(fig, use_container_width=True)
            
            # --- Render Alert Logs ---
            if len(st.session_state.alert_logs) > 0:
                log_df = pd.DataFrame(st.session_state.alert_logs).sort_values("Timestamp", ascending=False)
                log_container.dataframe(log_df, use_container_width=True, hide_index=True)
                
            # Yield slightly to prevent blocking
            time.sleep(0.01)
            
        except websocket.WebSocketConnectionClosedException:
            st.sidebar.error("Connection lost.")
            break
        except json.JSONDecodeError:
            continue
        except Exception as e:
            st.sidebar.error(f"Error: {e}")
            break
