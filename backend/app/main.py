import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Relative imports for the local package
from .generator import TelemetryGenerator
from .model import AnomalyDetector

detector = AnomalyDetector()
generator = TelemetryGenerator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing ML model and training on baseline data...")
    # Train the Isolation Forest model dynamically at startup
    detector.train_baseline(num_samples=1000)
    print("Training complete. Application ready.")
    yield
    print("Shutting down...")

app = FastAPI(
    title="Telemetry Anomaly Pipeline",
    description="Real-time telemetry ingestion and unsupervised anomaly detection.",
    lifespan=lifespan
)

# Allow CORS for the frontend dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health probe endpoint for container orchestration (e.g., Docker, K8s)."""
    return {
        "status": "healthy", 
        "model_trained": detector.is_trained
    }

@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """
    WebSocket endpoint that streams telemetry evaluated by the ML model
    in real-time at ~10Hz (100ms).
    """
    await websocket.accept()
    try:
        while True:
            # 1. Generate synthetic telemetry (5% chance of anomaly for demo purposes)
            raw_payload = generator.generate_payload(anomaly_prob=0.05)
            
            # 2. Evaluate the telemetry metrics using the unsupervised ML model
            evaluation = detector.evaluate(raw_payload["metrics"])
            
            # 3. Enrich payload with the model's analysis results
            enriched_payload = {
                **raw_payload,
                "analysis": evaluation
            }
            
            # 4. Stream to connected client
            await websocket.send_json(enriched_payload)
            
            # 10Hz streaming rate (100ms interval)
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
