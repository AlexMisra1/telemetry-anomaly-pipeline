import json
import time
import uuid
import random
from datetime import datetime, timezone
from typing import Dict, Any

class TelemetryGenerator:
    """
    Synthetic time-series generator for multi-sensor data.
    Simulates equipment readings: voltage, temperature, and vibration.
    """
    def __init__(self, 
                 base_voltage: float = 400.0, 
                 base_temp: float = 45.0, 
                 base_vibration: float = 0.5):
        self.base_voltage = base_voltage
        self.base_temp = base_temp
        self.base_vibration = base_vibration

    def generate_nominal(self) -> Dict[str, float]:
        """Generates nominal reading with slight gaussian noise."""
        return {
            "voltage": round(random.gauss(self.base_voltage, 2.0), 2),
            "temperature": round(random.gauss(self.base_temp, 1.0), 2),
            "vibration_rms": round(random.gauss(self.base_vibration, 0.05), 3)
        }
        
    def generate_anomaly(self, anomaly_type: str) -> Dict[str, float]:
        """Generates reading with specific anomaly characteristics."""
        if anomaly_type == "thermal_runaway":
            return {
                "voltage": round(random.gauss(self.base_voltage - 5.0, 3.0), 2),
                "temperature": round(random.gauss(self.base_temp + 35.0, 5.0), 2), 
                "vibration_rms": round(random.gauss(self.base_vibration + 0.1, 0.08), 3)
            }
        elif anomaly_type == "voltage_drop":
            return {
                "voltage": round(random.gauss(self.base_voltage - 80.0, 10.0), 2), 
                "temperature": round(random.gauss(self.base_temp + 2.0, 1.5), 2),
                "vibration_rms": round(random.gauss(self.base_vibration, 0.05), 3)
            }
        elif anomaly_type == "high_frequency_noise":
            return {
                "voltage": round(random.gauss(self.base_voltage, 5.0), 2),
                "temperature": round(random.gauss(self.base_temp, 1.0), 2),
                "vibration_rms": round(random.gauss(self.base_vibration + 3.0, 1.2), 3) 
            }
        else:
            return self.generate_nominal()

    def generate_payload(self, anomaly_prob: float = 0.0) -> Dict[str, Any]:
        """
        Generates a full JSON-serializable telemetry payload.
        Includes ISO timestamps, unique payload IDs, and optional injected anomalies.
        """
        is_anomaly = random.random() < anomaly_prob
        
        if is_anomaly:
            anomaly_type = random.choice(["thermal_runaway", "voltage_drop", "high_frequency_noise"])
            metrics = self.generate_anomaly(anomaly_type)
        else:
            anomaly_type = "none"
            metrics = self.generate_nominal()

        payload = {
            "payload_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "metadata": {
                "is_synthetic_anomaly": is_anomaly,
                "injected_anomaly_type": anomaly_type
            }
        }
        return payload

if __name__ == "__main__":
    # Test snippet
    generator = TelemetryGenerator()
    print("Generating 3 nominal samples:")
    for _ in range(3):
        print(json.dumps(generator.generate_payload(), indent=2))
    
    print("\nGenerating an anomaly sample:")
    print(json.dumps(generator.generate_payload(anomaly_prob=1.0), indent=2))
