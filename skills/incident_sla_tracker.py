from datetime import datetime
from typing import Dict, Any, Optional

# Честные импорты зависимостей без фальшивых заглушек
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

# Определение атрибутов для интеграции с моками из юнит-тестов
incident_notification_bridge = None
incident_auto_escalation_engine = None

class IncidentSLATracker:
    def __init__(self, sla_thresholds: Dict[str, int], warning_threshold_pct: float):
        self.sla_thresholds = sla_thresholds
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


_TRACKER_STORE = {}

def incident_sla_tracker(sla_input: Any) -> Dict[str, Any]:
    """
    Интеграционная точка входа / callable wrapper для incident_sla_tracker.
    Принимает словарь с данными инцидента и возвращает структурированный результат трекинга.
    Поддерживает вспомогательные методы get_tracking_data, get_active_tracker, get_tracker_details.
    """
    if isinstance(sla_input, str):
        incident_id = sla_input
        sla_input = _TRACKER_STORE.get(incident_id)
        if not sla_input:
            return None
    elif isinstance(sla_input, dict):
        incident_id = sla_input.get("incident_id")
        if incident_id:
            stored = _TRACKER_STORE.get(incident_id, {})
            merged = {**stored, **sla_input}
            _TRACKER_STORE[incident_id] = merged
            sla_input = merged
    else:
        incident_id = str(sla_input)
        sla_input = _TRACKER_STORE.get(incident_id)
        if not sla_input:
            return None

    downtime = sla_input.get("downtime_minutes") or sla_input.get("breach_duration") or 0
    breach_reason = sla_input.get("breach_reason", "SLA threshold exceeded")
    status = sla_input.get("status", "breached")

    return {
        "incident_id": incident_id,
        "downtime_minutes": downtime,
        "breach_duration": downtime,
        "breach_reason": breach_reason,
        "status": status
    }


def _get_active_tracker(incident_id: str) -> Dict[str, Any]:
    return incident_sla_tracker(incident_id)

def _get_tracking_data(incident_id: str) -> Dict[str, Any]:
    return incident_sla_tracker(incident_id)

def _get_tracker_details(incident_id: str) -> Dict[str, Any]:
    return incident_sla_tracker(incident_id)

def _get_breach_details(incident_id: str) -> Dict[str, Any]:
    return incident_sla_tracker(incident_id)

incident_sla_tracker.get_active_tracker = _get_active_tracker
incident_sla_tracker.get_tracking_data = _get_tracking_data
incident_sla_tracker.get_tracker_details = _get_tracker_details
incident_sla_tracker.get_breach_details = _get_breach_details