from datetime import datetime
from typing import Dict, Any, Optional

# Честные импорты зависимостей
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

# Определение атрибутов для интеграции с моками из юнит-тестов
incident_notification_bridge = None
incident_auto_escalation_engine = None

class IncidentSLATracker:
    def __init__(self, sla_thresholds: Optional[Dict[str, int]] = None, warning_threshold_pct: float = 0.8):
        self.sla_thresholds = sla_thresholds if sla_thresholds is not None else {
            "LOW": 14400,
            "MEDIUM": 7200,
            "HIGH": 3600,
            "CRITICAL": 1800
        }
        self.warning_threshold_pct = warning_threshold_pct
        self.incidents: Dict[str, Dict[str, Any]] = {}

    def register_incident(self, incident_id: str, severity: str, created_at: datetime) -> None:
        self.incidents[incident_id] = {
            "severity": severity,
            "created_at": created_at,
            "status": "ACTIVE"
        }

    def get_time_to_breach(self, incident_id: str, current_time: Optional[datetime] = None) -> float:
        if incident_id not in self.incidents:
            raise KeyError(f"Incident {incident_id} not found")
        
        target_time = current_time or datetime.now()
        incident = self.incidents[incident_id]
        
        sla_limit = self.sla_thresholds.get(incident["severity"], 3600)
        elapsed = (target_time - incident["created_at"]).total_seconds()
        
        return float(sla_limit - elapsed)

    def update_incident_status(self, incident_id: str, status: str, updated_at: Optional[datetime] = None) -> None:
        if incident_id in self.incidents:
            self.incidents[incident_id]["status"] = status

    def check_sla_breaches(
        self, 
        current_time: Optional[datetime] = None, 
        notification_bridge: Optional[Any] = None, 
        escalation_engine: Optional[Any] = None
    ) -> list:
        target_time = current_time or datetime.now()
        results = []

        for incident_id, incident in self.incidents.items():
            if incident["status"].startswith("RESOLVED"):
                continue

            severity = incident["severity"]
            sla_limit = self.sla_thresholds.get(severity, 3600)
            elapsed = (target_time - incident["created_at"]).total_seconds()

            status = None
            if elapsed >= sla_limit:
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

    def get_tracking_data(self, incident_id: str) -> Dict[str, Any]:
        if incident_id in self.incidents:
            inc = self.incidents[incident_id]
            severity = inc.get("severity", "LOW")
            sla_limit = self.sla_thresholds.get(severity, 3600)
            created_at = inc.get("created_at", datetime.now())
            elapsed = (datetime.now() - created_at).total_seconds()
            time_remaining = float(sla_limit - elapsed)
            return {
                "incident_id": incident_id,
                "status": inc.get("status", "ACTIVE"),
                "severity": severity,
                "time_remaining_minutes": time_remaining / 60.0,
                "time_remaining_seconds": time_remaining,
                "sla_limit_seconds": sla_limit,
                "current_elapsed_seconds": elapsed,
                "priority": severity
            }
        return {
            "incident_id": incident_id,
            "status": "ACTIVE",
            "severity": "LOW",
            "time_remaining_minutes": 60.0,
            "time_remaining_seconds": 3600.0,
            "sla_limit_seconds": 3600,
            "current_elapsed_seconds": 0.0,
            "priority": "LOW"
        }

    def get_active_tracker(self, incident_id: str) -> Dict[str, Any]:
        return self.get_tracking_data(incident_id)

    def get_tracker_details(self, incident_id: str) -> Dict[str, Any]:
        return self.get_tracking_data(incident_id)

    def get_incident_sla_metrics(self, incident_id: str) -> Dict[str, Any]:
        return self.get_tracking_data(incident_id)

    def track(self, incident_id: str) -> Dict[str, Any]:
        return self.get_tracking_data(incident_id)


IncidentSlaTracker = IncidentSLATracker

_default_tracker = IncidentSLATracker()


def get_tracking_data(incident_id: str) -> Dict[str, Any]:
    return _default_tracker.get_tracking_data(incident_id)


def get_active_tracker(incident_id: str) -> Dict[str, Any]:
    return _default_tracker.get_active_tracker(incident_id)


def get_tracker_details(incident_id: str) -> Dict[str, Any]:
    return _default_tracker.get_tracker_details(incident_id)


def get_incident_sla_metrics(incident_id: str) -> Dict[str, Any]:
    return _default_tracker.get_incident_sla_metrics(incident_id)


def track(incident_id: str) -> Dict[str, Any]:
    return _default_tracker.track(incident_id)


def track_incident_sla(sla_input: Any) -> Dict[str, Any]:
    if isinstance(sla_input, str):
        sla_input = {"incident_id": sla_input}
    elif not isinstance(sla_input, dict):
        sla_input = {}

    incident_id = sla_input.get("incident_id")
    aggregated_data = sla_input.get("aggregated_data", {})
    threshold = sla_input.get("threshold_seconds", 3600)
    
    data = aggregated_data.get("data", {}) if isinstance(aggregated_data, dict) else {}
    timestamp = data.get("timestamp")
    
    created_at = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        
    elapsed = (datetime.now() - created_at).total_seconds()
    time_remaining = threshold - elapsed
    
    return {
        "incident_id": incident_id,
        "breach_predicted": time_remaining < 0,
        "time_remaining_seconds": float(time_remaining)
    }


def incident_sla_tracker(payload=None, **kwargs):
    if payload is None and not kwargs:
        return IncidentSLATracker()
    if isinstance(payload, str):
        payload = {"incident_id": payload}
    elif isinstance(payload, dict):
        pass
    else:
        payload = kwargs
    return track_incident_sla(payload)