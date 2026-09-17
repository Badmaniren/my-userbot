from datetime import datetime
from typing import Dict, Any, Optional

# Честные импорты зависимостей
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

# Определение атрибутов для интеграции с моками из юнит-тестов
incident_notification_bridge = None
incident_auto_escalation_engine = None

_SHARED_INCIDENT_STORE: Dict[str, Dict[str, Any]] = {}


class IncidentSLATracker:
    def __init__(self, sla_thresholds: Optional[Dict[str, int]] = None, warning_threshold_pct: float = 0.8):
        self.sla_thresholds = sla_thresholds if sla_thresholds is not None else {"HIGH": 3600, "MEDIUM": 7200, "LOW": 14400}
        self.warning_threshold_pct = warning_threshold_pct
        self.incidents: Dict[str, Dict[str, Any]] = {}

    def save_incident_data(self, incident_id: str, data: Dict[str, Any]) -> None:
        if incident_id not in self.incidents:
            self.incidents[incident_id] = {}
        if isinstance(data, dict):
            self.incidents[incident_id].update(data)

        if incident_id not in _SHARED_INCIDENT_STORE:
            _SHARED_INCIDENT_STORE[incident_id] = {}
        if isinstance(data, dict):
            _SHARED_INCIDENT_STORE[incident_id].update(data)

    def get_incident_data(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return self.incidents.get(incident_id) or _SHARED_INCIDENT_STORE.get(incident_id)

    def register_incident(self, incident_id: str, severity: str, created_at: datetime) -> None:
        record = {
            "severity": severity,
            "created_at": created_at,
            "status": "ACTIVE"
        }
        self.incidents[incident_id] = record
        _SHARED_INCIDENT_STORE[incident_id] = record

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
        if incident_id in _SHARED_INCIDENT_STORE:
            _SHARED_INCIDENT_STORE[incident_id]["status"] = status

    def check_sla_breaches(
        self, 
        current_time: Optional[datetime] = None, 
        notification_bridge: Optional[Any] = None, 
        escalation_engine: Optional[Any] = None
    ) -> list:
        target_time = current_time or datetime.now()
        results = []

        for incident_id, incident in self.incidents.items():
            if not isinstance(incident, dict):
                continue
            if incident.get("status", "").startswith("RESOLVED"):
                continue

            severity = incident.get("severity")
            created_at = incident.get("created_at")
            if not severity or not created_at:
                continue

            sla_limit = self.sla_thresholds.get(severity, 3600)
            if target_time.tzinfo is not None and created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=target_time.tzinfo)
            elif target_time.tzinfo is None and created_at.tzinfo is not None:
                target_time = target_time.replace(tzinfo=created_at.tzinfo)
            elapsed = (target_time - created_at).total_seconds()

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


def track_incident_sla(sla_input: Dict[str, Any]) -> Dict[str, Any]:
    incident_id = sla_input.get("incident_id")
    aggregated_data = sla_input.get("aggregated_data", {})
    threshold = sla_input.get("threshold_seconds", 3600)
    
    data = aggregated_data.get("data", {})
    timestamp = data.get("timestamp")
    
    created_at = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        
    elapsed = (datetime.now() - created_at).total_seconds()
    time_remaining = threshold - elapsed
    
    return {
        "incident_id": incident_id,
        "breach_predicted": time_remaining < 0,
        "time_remaining_seconds": float(time_remaining)
    }