from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

# Notification / Escalation bridge attributes for mocking in unit tests
incident_notification_bridge = None
incident_auto_escalation_engine = None


class IncidentSLATracker:
    def __init__(
        self,
        sla_thresholds: Optional[Dict[str, int]] = None,
        warning_threshold_pct: float = 0.8,
    ):
        if sla_thresholds is None:
            sla_thresholds = {
                "CRITICAL": 1800,
                "HIGH": 3600,
                "MEDIUM": 7200,
                "LOW": 14400,
            }
        self.sla_thresholds = sla_thresholds
        self.warning_threshold_pct = warning_threshold_pct
        self.incidents: Dict[str, Dict[str, Any]] = {}

    def register_incident(
        self, incident_id: str, severity: str, created_at: datetime
    ) -> None:
        self.incidents[incident_id] = {
            "incident_id": incident_id,
            "severity": severity,
            "created_at": created_at,
            "status": "ACTIVE",
        }

    def get_time_to_breach(
        self, incident_id: str, current_time: Optional[datetime] = None
    ) -> float:
        if incident_id not in self.incidents:
            raise KeyError(f"Incident {incident_id} not found")

        if current_time is None:
            current_time = datetime.now()

        incident = self.incidents[incident_id]
        severity = incident["severity"]
        created_at = incident["created_at"]

        sla_limit = self.sla_thresholds.get(severity, 3600)
        elapsed = (current_time - created_at).total_seconds()

        return float(sla_limit - elapsed)

    def update_incident_status(
        self,
        incident_id: str,
        status: str,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if incident_id in self.incidents:
            self.incidents[incident_id]["status"] = status
            if updated_at is not None:
                self.incidents[incident_id]["updated_at"] = updated_at

    def check_sla_breaches(
        self,
        current_time: Optional[datetime] = None,
        notification_bridge: Optional[Any] = None,
        escalation_engine: Optional[Any] = None,
    ) -> List[Dict[str, Any]]:
        if current_time is None:
            current_time = datetime.now()

        results = []
        for incident_id, incident in self.incidents.items():
            status_val = incident.get("status", "ACTIVE")
            if isinstance(status_val, str) and status_val.startswith("RESOLVED"):
                continue

            severity = incident.get("severity", "MEDIUM")
            sla_limit = self.sla_thresholds.get(severity, 3600)
            created_at = incident.get("created_at")
            if not created_at:
                continue

            elapsed = (current_time - created_at).total_seconds()

            status = None
            if elapsed > sla_limit:
                status = "BREACHED"
                if notification_bridge:
                    notification_bridge.notify_sla_breach(
                        incident_id=incident_id, severity=severity
                    )
                if escalation_engine:
                    escalation_engine.escalate_incident(
                        incident_id=incident_id, severity=severity
                    )
            elif elapsed >= sla_limit * self.warning_threshold_pct:
                status = "WARNING"

            if status:
                results.append({"incident_id": incident_id, "status": status})

        return results

    def track(
        self, incident_id: str, actual_time: float, target_time: float
    ) -> Dict[str, Any]:
        breach = actual_time > target_time
        remaining = target_time - actual_time
        tracking_result = {
            "incident_id": incident_id,
            "actual_time": actual_time,
            "target_time": target_time,
            "breached": breach,
            "breach_predicted": breach,
            "time_remaining_seconds": remaining,
        }
        self.incidents[incident_id] = tracking_result
        return tracking_result

    def get_tracking_data(self, incident_id: Optional[str] = None) -> Any:
        if incident_id:
            return self.incidents.get(incident_id)
        return self.incidents

    def get_tracker_details(self) -> Dict[str, Any]:
        return {
            "sla_thresholds": self.sla_thresholds,
            "warning_threshold_pct": self.warning_threshold_pct,
            "tracked_incidents_count": len(self.incidents),
        }


IncidentSlaTracker = IncidentSLATracker

_ACTIVE_TRACKER = IncidentSLATracker()


def track_incident_sla(sla_input: Dict[str, Any]) -> Dict[str, Any]:
    incident_id = sla_input.get("incident_id")
    aggregated_data = sla_input.get("aggregated_data", {})
    threshold = sla_input.get("threshold_seconds", 3600)

    data = aggregated_data.get("data", {}) if isinstance(aggregated_data, dict) else {}
    timestamp = data.get("timestamp")

    if timestamp is None and isinstance(aggregated_data, dict):
        raw_data = aggregated_data.get("raw_data", {})
        if isinstance(raw_data, dict):
            timestamp = raw_data.get("timestamp")

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
        "time_remaining_seconds": time_remaining,
    }


def incident_sla_tracker(payload: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
    if payload is None and not kwargs:
        return _ACTIVE_TRACKER
    if isinstance(payload, dict):
        return track_incident_sla(payload)
    incident_id = payload if isinstance(payload, str) else kwargs.get("incident_id", "inc-default")
    actual_time = kwargs.get("actual_time", 0.0)
    target_time = kwargs.get("target_time", 3600.0)
    return _ACTIVE_TRACKER.track(incident_id, actual_time, target_time)


incident_sla_tracker.get_tracking_data = lambda incident_id=None: _ACTIVE_TRACKER.get_tracking_data(incident_id)
incident_sla_tracker.get_active_tracker = lambda: _ACTIVE_TRACKER
incident_sla_tracker.get_tracker_details = lambda: _ACTIVE_TRACKER.get_tracker_details()
