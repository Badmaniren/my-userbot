import io
import hashlib

from skills.system_health_telemetry_collector import (
    SystemHealthTelemetryCollector,
    system_health_telemetry_collector
)
from skills.system_risk_evaluator import (
    SystemRiskEvaluator,
    system_risk_evaluator
)
from skills.incident_trend_analyzer import (
    IncidentTrendAnalyzer,
    incident_trend_analyzer
)

class SecurityIncidentPredictor:
    def predict(self, metrics: dict, telemetry: dict) -> dict:
        if not metrics:
            return {
                "incident_probability": 0.0,
                "risk_score": 0.0,
                "analyzed_metrics": [],
                "telemetry_reference": telemetry.get("id", "")
            }

        analyzed_metrics = list(metrics.keys())
        first_key = analyzed_metrics[0]
        val = float(metrics[first_key])

        probability = min(max(val / 100.0, 0.0), 1.0)
        risk_score = val * 1.5

        return {
            "incident_probability": probability,
            "risk_score": risk_score,
            "analyzed_metrics": analyzed_metrics,
            "telemetry_reference": telemetry.get("id", "")
        }

    def _read_telemetry_stream(self, stream_data: io.BytesIO) -> io.BytesIO:
        return stream_data

    def evaluate_stream_risk(self, stream_data: io.BytesIO, vulnerability_score: int) -> dict:
        stream_bytes = stream_data.read()
        stream_hash = hashlib.sha256(stream_bytes).hexdigest()
        return {
            "processed": True,
            "vulnerability_score": vulnerability_score,
            "stream_hash": stream_hash
        }

    def _fetch_dynamic_threshold(self, metric_key: str) -> float:
        return 50.0

    def assess_anomaly(self, metrics: dict, metric_key: str) -> dict:
        actual_value = metrics.get(metric_key, 0.0)
        threshold = self._fetch_dynamic_threshold(metric_key)
        breach_detected = actual_value > threshold
        return {
            "breach_detected": breach_detected,
            "metric_key": metric_key,
            "threshold": threshold,
            "actual_value": actual_value
        }