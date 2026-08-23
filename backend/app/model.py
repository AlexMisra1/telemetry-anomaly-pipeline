import numpy as np
from typing import Dict, Any
from sklearn.ensemble import IsolationForest
import sys
import os

# To allow running directly or as a module
try:
    from .generator import TelemetryGenerator
except ImportError:
    from generator import TelemetryGenerator

class AnomalyDetector:
    """
    Unsupervised Isolation Forest anomaly detection engine.
    Trains on baseline nominal telemetry to learn normal operating boundaries.
    """
    def __init__(self, contamination: float = 0.05, n_estimators: int = 100):
        self.model = IsolationForest(
            n_estimators=n_estimators, 
            contamination=contamination, 
            random_state=42
        )
        self.is_trained = False
        
    def train_baseline(self, num_samples: int = 1000):
        """
        Pre-trains the model on generated nominal baseline data.
        """
        generator = TelemetryGenerator()
        training_data = []
        for _ in range(num_samples):
            # Baseline data should be nominal
            metrics = generator.generate_nominal()
            training_data.append([
                metrics["voltage"],
                metrics["temperature"],
                metrics["vibration_rms"]
            ])
            
        X_train = np.array(training_data)
        self.model.fit(X_train)
        self.is_trained = True
        
    def evaluate(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """
        Evaluates a real-time metrics payload.
        Returns anomaly decision, normalized score, and operational status.
        """
        if not self.is_trained:
            raise RuntimeError("AnomalyDetector must be trained before evaluation.")
            
        X_test = np.array([[
            metrics.get("voltage", 0.0),
            metrics.get("temperature", 0.0),
            metrics.get("vibration_rms", 0.0)
        ]])
        
        # predict: 1 for inlier, -1 for outlier
        prediction = self.model.predict(X_test)[0]
        
        # score_samples: opposite of anomaly score (lower/more negative == more anomalous)
        # Usually ranges from ~0.0 to -0.3. We map this to a 0.0 - 1.0 positive scale.
        raw_score = self.model.score_samples(X_test)[0]
        
        # Heuristic normalization (can be tuned based on data distribution)
        # Negate raw score, cap at 1.0. E.g., raw_score -0.15 -> score 0.15
        anomaly_score = min(max(-raw_score, 0.0), 1.0)
        
        is_anomaly = bool(prediction == -1)
        
        if is_anomaly:
            # Differentiate severity based on how far outside the boundary we are
            status = "CRITICAL" if anomaly_score > 0.15 else "WARNING"
        else:
            status = "NOMINAL"
            
        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(float(anomaly_score), 4),
            "status": status
        }
        
if __name__ == "__main__":
    detector = AnomalyDetector()
    print("Training baseline model (1000 samples)...")
    detector.train_baseline()
    print("Training complete.\n")
    
    gen = TelemetryGenerator()
    
    print("--- Evaluating Nominal Reading ---")
    nom_metrics = gen.generate_nominal()
    print(f"Metrics: {nom_metrics}")
    print(f"Evaluation: {detector.evaluate(nom_metrics)}\n")
    
    print("--- Evaluating Thermal Runaway Anomaly ---")
    anom_metrics = gen.generate_anomaly("thermal_runaway")
    print(f"Metrics: {anom_metrics}")
    print(f"Evaluation: {detector.evaluate(anom_metrics)}")
