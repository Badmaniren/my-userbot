import uuid
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger

class RepoHealthAnomalyInspector:
    def __init__(self, pulse_engine=None):
        self.pulse_engine = pulse_engine if pulse_engine is not None else RepoHealthPulseEngine()
        try:
            self.logger = RepoLogger(repo_path=".")
        except TypeError:
            self.logger = RepoLogger()

    def inspect(self, repo_id, pulse_payload=None, threshold=None):
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