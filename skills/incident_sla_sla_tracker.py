import time
from enum import Enum
import io

from skills.incident_aggregator import IncidentAggregator
from skills.incident_impact_analyzer import IncidentImpactAnalyzer

class SlaState(Enum):
    TRACKING = "TRACKING"
    VIOLATED = "VIOLATED"
    RESOLVED = "RESOLVED"

class SlaViolationException(Exception):
    pass

class IncidentSlaTracker:
    def __init__(self, incident_aggregator, incident_impact_analyzer):
        self.incident_aggregator = incident_aggregator
        self.impact_analyzer = incident_impact_analyzer
        self.active_slas = {}

    def initialize_incident_sla(self, incident_id):
        details = self.incident_aggregator.get_incident_details(incident_id)
        limit_seconds = self.impact_analyzer.calculate_urgency(details)
        start_time = time.time()

        self.active_slas[incident_id] = {
            "start_time": start_time,
            "limit_seconds": limit_seconds,
            "state": SlaState.TRACKING.value
        }

        return {
            "incident_id": incident_id,
            "state": SlaState.TRACKING.value,
            "limit_seconds": limit_seconds,
            "start_time": start_time
        }

    def check_violation(self, incident_id):
        if incident_id not in self.active_slas:
            raise KeyError(f"Incident {incident_id} not found in active SLAs.")

        sla = self.active_slas[incident_id]

        if hasattr(self.incident_aggregator, 'fetch_raw_telemetry'):
            self.incident_aggregator.fetch_raw_telemetry(incident_id)
        if hasattr(self.incident_aggregator, 'get_status_description'):
            self.incident_aggregator.get_status_description(incident_id)

        current_time = time.time()
        elapsed = current_time - sla["start_time"]

        if elapsed > sla["limit_seconds"]:
            sla["state"] = SlaState.VIOLATED.value
            return True

        return False

    def resolve_incident(self, incident_id, resolution_code):
        if incident_id not in self.active_slas:
            raise KeyError(f"Incident {incident_id} not found in active SLAs.")

        sla = self.active_slas[incident_id]
        sla["state"] = SlaState.RESOLVED.value

        return {
            "success": True,
            "resolution_code": resolution_code
        }

    def generate_sla_report(self):
        stream = self.impact_analyzer.export_metrics_stream()
        content = stream.read().decode('utf-8')
        report = {}
        for line in content.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                report[key] = val
        return report

def incident_sla_sla_tracker(payload=None, **kwargs):
    if isinstance(payload, dict):
        incident_id = payload.get("incident_id")
        time_budget_minutes = payload.get("time_budget_minutes", 60)
        deadline_timestamp = time.time() + (time_budget_minutes * 60)

        return {
            "incident_id": incident_id,
            "sla_status": SlaState.TRACKING.value,
            "deadline_timestamp": deadline_timestamp
        }
    return IncidentSlaTracker(
        kwargs.get("incident_aggregator", IncidentAggregator()),
        kwargs.get("incident_impact_analyzer", IncidentImpactAnalyzer())
    )