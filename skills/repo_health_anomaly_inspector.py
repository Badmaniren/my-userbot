import uuid
from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_logger import RepoLogger

class RepoHealthAnomalyInspector:
    def __init__(self, pulse_engine=None):
        self.pulse_engine = pulse_engine if pulse_engine is not None else RepoHealthPulseEngine()

    def inspect(self, repo_id, pulse_payload=None, threshold=None):
        metrics = {}
        if pulse_payload and isinstance(pulse_payload, dict) and "metrics" in pulse_payload:
            metrics = pulse_payload["metrics"]
        elif self.pulse_engine:
            try:
                metrics = self.pulse_engine.get_metrics(repo_id)
            except TypeError:
                pass

        anomalies = []
        is_anomaly = False
        max_deviation = 0.0

        for k, v in metrics.items():
            if isinstance(v, (int, float)):
                if v < 0:
                    anomalies.append({'metric': k, 'value': v, 'deviation': 'negative'})
                    is_anomaly = True
                if threshold is not None and v < threshold:
                    is_anomaly = True
                    dev = float(abs(threshold - v))
                    if dev > max_deviation:
                        max_deviation = dev

        return {
            'repo_id': repo_id,
            'anomalies': anomalies,
            'status': 'inspected',
            'is_anomaly': is_anomaly,
            'deviation_score': max_deviation if max_deviation > 0 else (float(len(anomalies)) if anomalies else 0.0)
        }