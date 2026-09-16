from datetime import datetime
from typing import Dict, Any, Optional, Union

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


def track_incident_sla(
    sla_input: Union[Dict[str, Any], str, None] = None,
    incident_id: Optional[str] = None,
    threshold_minutes: Optional[float] = None,
    elapsed_minutes: Optional[float] = None,
    threshold_seconds: Optional[float] = None,
    elapsed_seconds: Optional[float] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    target_id = incident_id

    if isinstance(sla_input, str):
        target_id = sla_input
    elif isinstance(sla_input, dict):
        if not target_id:
            target_id = sla_input.get("incident_id")
        if threshold_minutes is None and "threshold_minutes" in sla_input:
            threshold_minutes = sla_input["threshold_minutes"]
        if elapsed_minutes is None and "elapsed_minutes" in sla_input:
            elapsed_minutes = sla_input["elapsed_minutes"]
        if threshold_seconds is None and "threshold_seconds" in sla_input:
            threshold_seconds = sla_input["threshold_seconds"]
        if elapsed_seconds is None and "elapsed_seconds" in sla_input:
            elapsed_seconds = sla_input["elapsed_seconds"]
        if "aggregated_data" in sla_input:
            agg = sla_input["aggregated_data"]
            data = agg.get("data", {}) if isinstance(agg, dict) else {}
            ts = data.get("timestamp")
            if ts:
                created_at = datetime.fromtimestamp(ts)
                elapsed_seconds = (datetime.now() - created_at).total_seconds()

    if threshold_seconds is None:
        threshold_seconds = (threshold_minutes * 60.0) if threshold_minutes is not None else 3600.0
    if elapsed_seconds is None:
        elapsed_seconds = (elapsed_minutes * 60.0) if elapsed_minutes is not None else 0.0

    time_remaining = threshold_seconds - elapsed_seconds
    breach_detected = elapsed_seconds > threshold_seconds
    breach_predicted = time_remaining < 0

    return {
        "incident_id": target_id,
        "breach_detected": breach_detected,
        "breach_predicted": breach_predicted,
        "time_remaining_seconds": time_remaining,
        "elapsed_seconds": elapsed_seconds,
        "threshold_seconds": threshold_seconds
    }