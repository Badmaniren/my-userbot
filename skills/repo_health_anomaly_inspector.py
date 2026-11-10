from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger


class RepoHealthAnomalyInspector:
    def __init__(self, pulse_engine=None):
        self.pulse_engine = pulse_engine if pulse_engine is not None else RepoHealthPulseEngine()
        self.logger = RepoLogger(repo_path=".")

    def inspect(self, repo_id=None, pulse_payload=None, threshold=None):
        if pulse_payload is None:
            if repo_id is None:
                repo_id = "default-repo"
            if hasattr(self.pulse_engine, "get_pulse"):
                pulse_payload = self.pulse_engine.get_pulse(repo_id)
            elif hasattr(self.pulse_engine, "pulse"):
                pulse_payload = self.pulse_engine.pulse(repo_id)
            else:
                pulse_payload = {}

        if pulse_payload is None:
            pulse_payload = {}

        if not isinstance(pulse_payload, dict):
            pulse_payload = {}

        if repo_id is None:
            repo_id = pulse_payload.get("repo_id", "default-repo")

        metrics = pulse_payload.get("metrics", {})
        if not isinstance(metrics, dict):
            metrics = {}

        anomalies = []
        deviation_score = 0.0

        for metric_name, value in metrics.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                # Приводим к float для точной математики и предотвращения проблем типизации
                f_val = float(value)
                if f_val < 0:
                    anomalies.append({
                        "metric": metric_name,
                        "value": f_val,
                        "deviation": "negative"
                    })
                    deviation_score += abs(f_val)
                elif threshold is not None and f_val > float(threshold):
                    anomalies.append({
                        "metric": metric_name,
                        "value": f_val,
                        "deviation": "high"
                    })
                    deviation_score += f_val - float(threshold)

        is_anomaly = len(anomalies) > 0

        return {
            "repo_id": repo_id,
            "status": "inspected",
            "is_anomaly": is_anomaly,
            "anomalies": anomalies,
            "deviation_score": deviation_score
        }