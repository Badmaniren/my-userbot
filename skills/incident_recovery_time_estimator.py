import json
import io
import uuid
import requests

from skills import system_health_telemetry_collector
from skills.incident_aggregator import aggregate_incident
from skills.system_health_telemetry_collector import collect_telemetry


class IncidentRecoveryTimeEstimator:
    def _fetch_historical_data(self, severity):
        url = f"https://api.internal/incidents/history?severity={severity}"
        try:
            response = requests.get(url)
            if response and getattr(response, "status_code", None) == 200:
                raw = getattr(response, "raw", None)
                if raw and hasattr(raw, "read"):
                    content = raw.read()
                elif hasattr(response, "content"):
                    content = getattr(response, "content", b"")
                else:
                    content = None

                if content:
                    if isinstance(content, bytes):
                        content = content.decode('utf-8')
                    data = json.loads(content) if isinstance(content, str) else content
                    if isinstance(data, list):
                        return data
                    return [data]
        except (requests.RequestException, json.JSONDecodeError, AttributeError):
            return []
        return []

    def _get_current_system_load(self):
        try:
            stream = system_health_telemetry_collector.stream_metrics()
            if stream:
                line = stream.readline()
                if isinstance(line, bytes):
                    line = line.decode('ascii', errors='ignore')
                if '=' in line:
                    _, val = line.strip().split('=', 1)
                    return float(val)
        except (AttributeError, ValueError):
            return 50.0
        return 50.0

    def _calculate_confidence(self, data_points_count, variance):
        base = min(1.0, data_points_count / 50.0)
        penalty = min(0.5, variance / 10.0)
        conf = base - penalty
        return max(0.01, min(1.0, float(conf)))

    def estimate(self, incident_id, severity):
        history = self._fetch_historical_data(severity)
        load = self._get_current_system_load()

        if not history:
            return {
                "estimated_hours": 24.0,
                "confidence_score": 0.1
            }

        durations = [h.get("duration_hours", 12.0) for h in history]
        avg_duration = sum(durations) / len(durations)

        load_factor = 1.0 + (load / 100.0)
        estimated_hours = avg_duration * load_factor

        variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations) if durations else 1.0
        confidence = self._calculate_confidence(len(history), variance)

        return {
            "estimated_hours": float(estimated_hours),
            "confidence_score": float(confidence)
        }


def estimate_recovery_time(aggregated_incident, telemetry_data):
    if isinstance(aggregated_incident, dict):
        incident_id = aggregated_incident.get("id", str(uuid.uuid4()))
        metric = float(aggregated_incident.get("metric", 50.0))
    else:
        incident_id = str(uuid.uuid4())
        metric = 50.0

    estimated_minutes = int(metric * 1.5)
    if estimated_minutes <= 0:
        estimated_minutes = 30

    return {
        "incident_id": incident_id,
        "estimated_minutes": estimated_minutes
    }


incident_recovery_time_estimator = IncidentRecoveryTimeEstimator
