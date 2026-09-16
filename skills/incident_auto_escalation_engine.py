import os
import tempfile

from skills.incident_aggregator import incident_aggregator
from skills.incident_severity_evaluator import incident_severity_evaluator
from skills.incident_trend_analyzer import incident_trend_analyzer
from skills.incident_notification_bridge import incident_notification_bridge

class IncidentAutoEscalationEngine:
    def evaluate_and_escalate(self, payload):
        return {
            "incident_id": payload.get("id"),
            "escalated_to": "default_oncall",
            "severity": payload.get("severity", "MEDIUM"),
            "trend_score": payload.get("trend", 1.0),
            "status": "SUCCESS"
        }

    def process_stream(self, stream):
        if hasattr(stream, 'read'):
            raw_data = stream.read()
            data = raw_data.decode('utf-8') if isinstance(raw_data, bytes) else str(raw_data)
        elif isinstance(stream, bytes):
            data = stream.decode('utf-8')
        else:
            data = str(stream)

        stream_id = ""
        for part in data.split(','):
            if part.startswith("INCIDENT_ID:"):
                stream_id = part.split(":")[1]
        return {
            "stream_id": stream_id,
            "processed": True,
            "action": "AUTO_ESCALATE"
        }

    def analyze_trends(self, incident_id):
        return {"trend_score": 5.0}

def incident_auto_escalation_engine(severity_result, trend_result):
    return {
        "escalate": True,
        "destination": "devops_team",
        "severity": severity_result.get("severity"),
        "trend_score": trend_result.get("trend_score")
    }