import uuid
from typing import Optional, List, Dict, Any
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger

class RepoHealthAnomalyInspector:
    def __init__(self, pulse_engine=None, threshold_cpu: float = 80.0, threshold_error: float = 5.0):
        self.pulse_engine = pulse_engine if pulse_engine is not None else RepoHealthPulseEngine()
        self.threshold_cpu = threshold_cpu
        self.threshold_error = threshold_error
        try:
            self.logger = RepoLogger(repo_path=".")
        except TypeError:
            self.logger = RepoLogger()

    def inspect(self, repo_id=None, pulse_payload=None, threshold=None):
        if isinstance(repo_id, list):
            anomalies = []
            for record in repo_id:
                if isinstance(record, dict):
                    cpu = record.get("cpu_load", 0.0)
                    err = record.get("error_rate", 0.0)
                    if cpu > self.threshold_cpu or err > self.threshold_error:
                        anomalies.append(record)
            return anomalies
        if pulse_payload is None:
            if hasattr(self.pulse_engine, "get_pulse"):
                pulse_payload = self.pulse_engine.get_pulse(repo_id)
            elif hasattr(self.pulse_engine, "pulse"):
                pulse_payload = self.pulse_engine.pulse(repo_id)
            else:
                pulse_payload = {}

        if pulse_payload is None:
            pulse_payload = {}

        metrics = pulse_payload.get("metrics", {})
        anomalies = []
        deviation_score = 0.0

        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)):
                if value < 0:
                    anomalies.append({
                        "metric": metric_name,
                        "value": value,
                        "deviation": "negative"
                    })
                    deviation_score += abs(value)
                elif threshold is not None and value > threshold:
                    anomalies.append({
                        "metric": metric_name,
                        "value": value,
                        "deviation": "high"
                    })
                    deviation_score += value - threshold

        is_anomaly = len(anomalies) > 0

        return {
            "repo_id": repo_id,
            "status": "inspected",
            "is_anomaly": is_anomaly,
            "anomalies": anomalies,
            "deviation_score": deviation_score
        }


class AnomalyInspector(RepoHealthAnomalyInspector):
    def __init__(self, threshold_cpu: float = 80.0, threshold_error: float = 5.0, pulse_engine=None):
        super().__init__(pulse_engine=pulse_engine, threshold_cpu=threshold_cpu, threshold_error=threshold_error)