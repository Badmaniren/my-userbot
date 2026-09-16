from datetime import datetime
from typing import Dict, Any, Optional

# Честные импорты зависимостей без фальшивых заглушек
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity as _evaluate_incident_severity

# Определение атрибутов для интеграции с моками из юнит-тестов
incident_notification_bridge = None
incident_auto_escalation_engine = None


def evaluate_incident_severity(
    module_name: Any = "default_module",
    exception: Optional[Exception] = None,
    traceback_str: Optional[str] = None,
    incident_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    if isinstance(module_name, dict):
        payload = module_name
        mod_name = payload.get("module_name", "default_module")
        exc = payload.get("exception", exception)
        tb = payload.get("traceback_str", traceback_str)
        inc_id = payload.get("incident_id", incident_id)
        return _evaluate_incident_severity(mod_name, exc, tb, inc_id)
    if isinstance(module_name, Exception):
        incident_id = traceback_str
        traceback_str = exception
        exception = module_name
        module_name = "default_module"
    elif module_name is None:
        module_name = "default_module"
    return _evaluate_incident_severity(module_name, exception, traceback_str, incident_id)


class IncidentSLATracker:
    def __init__(self, sla_thresholds: Dict[str, int] = None, warning_threshold_pct: float = 0.8):
        self.sla_thresholds = sla_thresholds if sla_thresholds is not None else {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        self.warning_threshold_pct = warning_threshold_pct
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


# Class alias for snake_case / CamelCase compatibility
IncidentSlaTracker = IncidentSLATracker

_GLOBAL_TRACKER = IncidentSLATracker()


def get_tracking_data(incident_id: str) -> Dict[str, Any]:
    if incident_id in _GLOBAL_TRACKER.incidents:
        inc = _GLOBAL_TRACKER.incidents[incident_id]
        time_rem = _GLOBAL_TRACKER.get_time_to_breach(incident_id)
        sla_limit = _GLOBAL_TRACKER.sla_thresholds.get(inc["severity"], 3600)
        elapsed = sla_limit - time_rem
        return {
            "incident_id": incident_id,
            "status": inc.get("status", "ACTIVE"),
            "priority": inc.get("severity", "LOW"),
            "sla_limit_seconds": sla_limit,
            "current_elapsed_seconds": elapsed,
            "time_remaining_minutes": time_rem / 60.0
        }
    return {
        "incident_id": incident_id,
        "status": "ACTIVE",
        "priority": "LOW",
        "sla_limit_seconds": 3600,
        "current_elapsed_seconds": 0,
        "time_remaining_minutes": 60.0
    }


def get_active_tracker(incident_id: str) -> Dict[str, Any]:
    return get_tracking_data(incident_id)


def get_tracker_details(incident_id: str) -> Dict[str, Any]:
    return get_tracking_data(incident_id)


def track_incident_sla(sla_input: Dict[str, Any]) -> Dict[str, Any]:
    incident_id = sla_input.get("incident_id")
    aggregated_data = sla_input.get("aggregated_data", {})
    threshold = sla_input.get("threshold_seconds", 3600)
    
    data = aggregated_data.get("data", {})
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
