# 🛰️ Telemetry Ingestion & Anomaly Detection Pipeline

A production-grade, real-time streaming pipeline that generates synthetic equipment telemetry (voltage, temperature, vibration), evaluates the readings using unsupervised Machine Learning (Isolation Forests), and streams the analyzed payload to a live dashboard via WebSockets.

Designed specifically to highlight modern distributed systems architectures and time-series ML, relevant for EV battery monitoring, aerospace avionics, and industrial IoT.

## 🏗️ System Architecture

```text
  [ Synthetic Telemetry Generator ] 
               | (~10Hz JSON Streams)
               v
  +-------------------------+        +--------------------------+
  |    FastAPI Backend      |        |   Unsupervised ML Engine |
  |-------------------------|        |--------------------------|
  | - REST Health Probes    | <----> | - Isolation Forest       |
  | - WebSocket Streamer    |        | - Rolling Z-Score Bounds |
  +-------------------------+        +--------------------------+
               | (WebSocket /ws/telemetry)
               v
  +-------------------------+
  |  Streamlit Dashboard    |
  |-------------------------|
  | - Live KPIs             |
  | - Rolling Plotly Charts |
  | - Anomaly Alert Logs    |
  +-------------------------+
```

## 🚀 1-Step Setup

Ensure you have Docker and Docker Compose installed.

```bash
docker-compose up --build
```

- **Frontend Dashboard:** [http://localhost:8501](http://localhost:8501)
- **Backend API:** [http://localhost:8000/docs](http://localhost:8000/docs)

## 🧠 Technical Highlights

- **Ultra-Low Latency Streaming:** Leverages `fastapi` WebSockets to stream JSON payloads at ~10Hz (100ms intervals).
- **Unsupervised Anomaly Detection:** Implements `scikit-learn`'s `IsolationForest`, dynamically trained at startup on baseline nominal sensor data to establish operational boundaries without labeled data.
- **Microservices & Orchestration:** Fully containerized architecture using Docker and `docker-compose`, featuring inter-service networking and explicit healthcheck dependency gating.
- **Domain Relevance (EV/Aerospace):** Accurately models real-world fault conditions like *thermal runaway*, *voltage drops*, and *high-frequency RMS vibration bursts*.
- **Reactive UI:** The `streamlit` frontend uses a polling WebSocket loop combined with rolling data queues (`collections.deque`) and `plotly` to render high-throughput charts without memory leaks.
