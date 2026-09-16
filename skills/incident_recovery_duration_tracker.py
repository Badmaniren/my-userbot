import io
import json
import os
from skills.incident_aggregator import get_incident_data, store_incident_metrics

class IncidentRecoveryDurationTracker:
    def __init__(self, incident_aggregator=None):
        self.aggregator = incident_aggregator

    def calculate_recovery_duration(self, incident_id):
        if self.aggregator and hasattr(self.aggregator, "get_incident_data"):
            data = self.aggregator.get_incident_data(incident_id)
        else:
            data = get_incident_data(incident_id)

        if not data:
            raise ValueError("Incident not found")

        duration = data["end_timestamp"] - data["start_timestamp"]
        return duration

    def track_downtime(self, incident_id):
        stream = self._fetch_raw_logs(incident_id)
        self._process_stream(stream)
        if self.aggregator and hasattr(self.aggregator, "get_downtime_metrics"):
            metrics = self.aggregator.get_downtime_metrics(incident_id)
            return metrics["duration"]
        return 0.0

    def generate_recovery_report(self, incident_id):
        duration = self.calculate_recovery_duration(incident_id)
        return {
            "incident_id": incident_id,
            "duration": float(duration)
        }

    def _fetch_raw_logs(self, incident_id):
        return io.BytesIO(b"LOG_ENTRY_DATA")

    def _process_stream(self, stream):
        if hasattr(stream, "read"):
            content = stream.read()
            if isinstance(content, bytes):
                return content.decode('utf-8', errors='replace')
            return str(content)
        return str(stream)

def track_recovery_duration(incident_id):
    data = get_incident_data(incident_id)
    if not data:
        return None

    duration = data["end_timestamp"] - data["start_timestamp"]

    data['recovery_duration'] = duration
    store_incident_metrics(data)

    report_path = f"recovery_log_{incident_id}.json"
    with open(report_path, 'w') as f:
        json.dump({"incident_id": incident_id, "recovery_duration": duration}, f)

    return {
        "incident_id": incident_id,
        "duration_seconds": duration
    }

incident_recovery_duration_tracker = IncidentRecoveryDurationTracker
