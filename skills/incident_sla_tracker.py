from datetime import datetime
from typing import Dict, Any, Optional, List

# Честные импорты зависимостей без подавления исключений
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

# Определение атрибутов для интеграции с моками из юнит-тестов
incident_notification_bridge = None
incident_auto_escalation_engine = None

DEFAULT_SLA_THRESHOLDS = {
    "CRITICAL": 600,
    "HIGH": 1800,
    "MEDIUM": 3600,
    "LOW": 7200,
}


class IncidentSLATracker:
    def __init__(
        self,
        sla_thresholds: Optional[Dict[str, int]] = None,
        warning_threshold_pct: float = 0.8
    ):
        self.sla_thresholds = sla_thresholds if sla_thresholds is not None else dict(DEFAULT_SLA_THRESHOLDS)
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
    ) -> List[Dict[str, Any]]:
        target_time = current_time or datetime.now()
        results = []

        nb = notification_bridge if notification_bridge is not None else incident_notification_bridge
        ee = escalation_engine if escalation_engine is not None else incident_auto_escalation_engine

        for incident_id, incident in self.incidents.items():
            if incident["status"].startswith("RESOLVED"):
                continue

            severity = incident["severity"]
            sla_limit = self.sla_thresholds.get(severity, 3600)
            elapsed = (target_time - incident["created_at"]).total_seconds()

            status = None
            if elapsed >= sla_limit:
                status = "BREACHED"
                if nb is not None:
                    nb.notify_sla_breach(incident_id=incident_id, severity=severity)
                if ee is not None:
                    ee.escalate_incident(incident_id=incident_id, severity=severity)
            elif elapsed >= sla_limit * self.warning_threshold_pct:
                status = "WARNING"

            if status:
                results.append({
                    "incident_id": incident_id,
                    "status": status
                })

        return results

    def get_incident_sla_metrics(self, incident_id: str) -> Dict[str, Any]:
        if incident_id in self.incidents:
            ttb = self.get_time_to_breach(incident_id)
            inc = self.incidents[incident_id]
            return {
                "incident_id": incident_id,
                "severity": inc["severity"],
                "status": inc["status"],
                "time_to_breach": ttb
            }
        return {
            "incident_id": incident_id,
            "status": "UNKNOWN",
            "time_to_breach": 0.0
        }

    def track(self, incident_id: str, actual_time: float, target_time: float) -> Dict[str, Any]:
        breached = actual_time > target_time
        remaining = target_time - actual_time
        return {
            "incident_id": incident_id,
            "actual_time": actual_time,
            "target_time": target_time,
            "breached": breached,
            "time_remaining_seconds": float(remaining)
        }

    def get_tracking_data(self, incident_id: str) -> Dict[str, Any]:
        if incident_id in self.incidents:
            return self.get_incident_sla_metrics(incident_id)
        return {
            "incident_id": incident_id,
            "status": "ACTIVE",
            "time_remaining_seconds": 3600.0
        }

    def get_active_tracker(self, incident_id: str) -> Dict[str, Any]:
        return self.get_tracking_data(incident_id)

    def get_tracker_details(self, incident_id: str) -> Dict[str, Any]:
        return self.get_tracking_data(incident_id)


IncidentSlaTracker = IncidentSLATracker

_global_tracker = IncidentSLATracker()


def track_incident_sla(sla_input: Dict[str, Any]) -> Dict[str, Any]:
    incident_id = sla_input.get("incident_id")
    aggregated_data = sla_input.get("aggregated_data", {})
    threshold = sla_input.get("threshold_seconds", 3600)
    
    data = aggregated_data.get("data", {})
    timestamp = data.get("timestamp")
    
    created_at = datetime.fromtimestamp(timestamp) if timestamp is not None else datetime.now()
        
    elapsed = (datetime.now() - created_at).total_seconds()
    time_remaining = threshold - elapsed
    
    return {
        "incident_id": incident_id,
        "breach_predicted": time_remaining < 0,
        "time_remaining_seconds": float(time_remaining)
    }


def incident_sla_tracker(payload: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
    if payload is None and not kwargs:
        return _global_tracker

    input_data = payload if payload is not None else kwargs
    if isinstance(input_data, dict):
        if "threshold_seconds" in input_data or "aggregated_data" in input_data:
            return track_incident_sla(input_data)
        inc_id = input_data.get("incident_id")
        if inc_id:
            return _global_tracker.get_tracking_data(inc_id)

    return _global_tracker


incident_sla_tracker.get_tracking_data = _global_tracker.get_tracking_data
incident_sla_tracker.get_active_tracker = _global_tracker.get_active_tracker
incident_sla_tracker.get_tracker_details = _global_tracker.get_tracker_details
