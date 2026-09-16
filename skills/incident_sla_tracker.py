from datetime import datetime
from typing import Dict, Any, Optional

from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

# Attributes for test mocking integration
incident_notification_bridge = None
incident_auto_escalation_engine = None

DEFAULT_SLA_THRESHOLDS = {
    "CRITICAL": 300,
    "HIGH": 1800,
    "MEDIUM": 7200,
    "LOW": 28800
}


class IncidentSLATracker:
    def __init__(
        self,
        sla_thresholds: Optional[Dict[str, int]] = None,
        warning_threshold_pct: Optional[float] = None
    ):
        self.sla_thresholds = sla_thresholds if sla_thresholds is not None else DEFAULT_SLA_THRESHOLDS.copy()
        self.warning_threshold_pct = warning_threshold_pct if warning_threshold_pct is not None else 0.8
        self.incidents = {}

    def register_incident(self, incident_id: str, severity: str, created_at: datetime) -> None:
        self.incidents[incident_id] = {
            "severity": severity,
            "created_at": created_at,
            "status": "ACTIVE"
        }

    def get_time_to_breach(self, incident_id: str, current_time: Optional[datetime] = None) -> float:
        if incident_id not in self.incidents:
            raise KeyError(f"Incident {incident_id} not found")
        
        if current_time is None:
            current_time = datetime.now()
            
        incident = self.incidents[incident_id]
        severity = incident["severity"]
        created_at = incident["created_at"]
        
        sla_limit = self.sla_thresholds.get(severity, 3600)
        elapsed = (current_time - created_at).total_seconds()
        
        return sla_limit - elapsed

    def update_incident_status(self, incident_id: str, status: str, updated_at: Optional[datetime] = None) -> None:
        if incident_id in self.incidents:
            self.incidents[incident_id]["status"] = status

    def check_sla_breaches(
        self, 
        current_time: Optional[datetime] = None, 
        notification_bridge: Optional[Any] = None, 
        escalation_engine: Optional[Any] = None
    ) -> list:
        if current_time is None:
            current_time = datetime.now()

        results = []
        for incident_id, incident in self.incidents.items():
            if incident["status"].startswith("RESOLVED"):
                continue

            severity = incident["severity"]
            sla_limit = self.sla_thresholds.get(severity, 3600)
            created_at = incident["created_at"]
            elapsed = (current_time - created_at).total_seconds()

            status = None
            if elapsed > sla_limit:
                status = "BREACHED"
                if notification_bridge:
                    notification_bridge.notify_sla_breach(incident_id=incident_id, severity=severity)
                if escalation_engine:
                    escalation_engine.escalate_incident(incident_id=incident_id, severity=severity)
            elif elapsed >= sla_limit * self.warning_threshold_pct:
                status = "WARNING"

            if status:
                results.append({
                    "incident_id": incident_id,
                    "status": status
                })

        return results

    def track(self, incident_id: str, actual_time: float, target_time: float) -> Dict[str, Any]:
        is_breached = actual_time > target_time
        time_remaining = max(0.0, target_time - actual_time)
        return {
            "incident_id": incident_id,
            "actual_time": actual_time,
            "target_time": target_time,
            "is_breached": is_breached,
            "time_remaining_seconds": time_remaining
        }


IncidentSlaTracker = IncidentSLATracker


def track_incident_sla(sla_input: Any, actual_time: Optional[float] = None, target_time: Optional[float] = None) -> Dict[str, Any]:
    if isinstance(sla_input, str):
        inc_id = sla_input
        act = actual_time if actual_time is not None else 0.0
        tgt = target_time if target_time is not None else 3600.0
        return {
            "incident_id": inc_id,
            "actual_time": act,
            "target_time": tgt,
            "is_breached": act > tgt,
            "breach_predicted": act > tgt,
            "time_remaining_seconds": max(0.0, tgt - act)
        }
    elif isinstance(sla_input, dict):
        incident_id = sla_input.get("incident_id")
        aggregated_data = sla_input.get("aggregated_data", {})
        threshold = sla_input.get("threshold_seconds", 3600)

        data = aggregated_data.get("data", {}) if isinstance(aggregated_data, dict) else {}
        timestamp = data.get("timestamp")
        
        if timestamp:
            created_at = datetime.fromtimestamp(timestamp)
        else:
            created_at = datetime.now()

        elapsed = (datetime.now() - created_at).total_seconds()
        time_remaining = threshold - elapsed
        breach_predicted = time_remaining < 0

        return {
            "incident_id": incident_id,
            "breach_predicted": breach_predicted,
            "time_remaining_seconds": time_remaining
        }
    return {"incident_id": str(sla_input), "breach_predicted": False, "time_remaining_seconds": 0.0}


def incident_sla_tracker(payload=None, **kwargs):
    if payload is None and not kwargs:
        return IncidentSLATracker()
    if isinstance(payload, dict):
        if "sla_thresholds" in payload or "warning_threshold_pct" in payload:
            return IncidentSLATracker(
                sla_thresholds=payload.get("sla_thresholds"),
                warning_threshold_pct=payload.get("warning_threshold_pct")
            )
        return track_incident_sla(payload)
    if isinstance(payload, str):
        return track_incident_sla(payload, kwargs.get("actual_time"), kwargs.get("target_time"))
    return IncidentSLATracker(**kwargs)


def _get_tracking_data(incident_id=None):
    return {"status": "active", "incident_id": incident_id}


def _get_active_tracker():
    return IncidentSLATracker()


def _get_tracker_details(incident_id=None):
    return {"incident_id": incident_id, "tracking": True}


incident_sla_tracker.get_tracking_data = _get_tracking_data
incident_sla_tracker.get_active_tracker = _get_active_tracker
incident_sla_tracker.get_tracker_details = _get_tracker_details
