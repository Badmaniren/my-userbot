from datetime import datetime
from typing import Dict, Any, Optional

# Честные импорты зависимостей
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

# Определение атрибутов для интеграции с моками из юнит-тестов
incident_notification_bridge = None
incident_auto_escalation_engine = None

DEFAULT_SLA_THRESHOLDS = {
    "LOW": 7200,
    "MEDIUM": 3600,
    "HIGH": 1800,
    "CRITICAL": 600,
}

class IncidentSLATracker:
    def __init__(
        self,
        sla_thresholds: Optional[Dict[str, int]] = None,
        warning_threshold_pct: float = 0.8
    ):
        if sla_thresholds is None:
            self.sla_thresholds = dict(DEFAULT_SLA_THRESHOLDS)
        else:
            self.sla_thresholds = sla_thresholds
        self.warning_threshold_pct = warning_threshold_pct
        self.incidents: Dict[str, Dict[str, Any]] = {}

    def register_incident(self, incident_id: str, severity: str, created_at: Optional[datetime] = None) -> None:
        if created_at is None:
            created_at = datetime.now()
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

    def get_incident_sla_metrics(self, incident_id: str) -> Dict[str, Any]:
        if incident_id not in self.incidents:
            return {}
        incident = self.incidents[incident_id]
        time_to_breach = self.get_time_to_breach(incident_id)
        sla_limit = self.sla_thresholds.get(incident["severity"], 3600)
        return {
            "incident_id": incident_id,
            "severity": incident.get("severity"),
            "status": incident.get("status"),
            "created_at": incident.get("created_at"),
            "time_to_breach": time_to_breach,
            "sla_limit_seconds": sla_limit,
            "is_breached": time_to_breach <= 0,
        }

    def track(self, incident_id: str, actual_time: float = 0.0, target_time: float = 0.0) -> Dict[str, Any]:
        if target_time <= 0:
            if incident_id in self.incidents:
                severity = self.incidents[incident_id].get("severity", "MEDIUM")
                target_time = float(self.sla_thresholds.get(severity, 3600))
            else:
                target_time = 3600.0
        time_remaining = target_time - actual_time
        return {
            "incident_id": incident_id,
            "actual_time": actual_time,
            "target_time": target_time,
            "time_remaining_seconds": float(time_remaining),
            "breach_predicted": time_remaining < 0,
            "status": "BREACHED" if time_remaining < 0 else "OK"
        }

    def get_telemetry(self) -> Dict[str, Any]:
        return {
            "total_tracked": len(self.incidents),
            "active_incidents": sum(1 for inc in self.incidents.values() if inc.get("status") == "ACTIVE"),
            "thresholds": self.sla_thresholds,
            "warning_threshold_pct": self.warning_threshold_pct
        }

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


# Class alias
IncidentSlaTracker = IncidentSLATracker


def track_incident_sla(sla_input: Dict[str, Any]) -> Dict[str, Any]:
    incident_id = sla_input.get("incident_id")
    aggregated_data = sla_input.get("aggregated_data", {})
    threshold = sla_input.get("threshold_seconds", 3600)
    
    data = aggregated_data.get("data", {}) if isinstance(aggregated_data, dict) else {}
    timestamp = data.get("timestamp")
    
    if not timestamp and isinstance(aggregated_data, dict):
        timestamp = aggregated_data.get("timestamp")

    created_at = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        
    elapsed = (datetime.now() - created_at).total_seconds()
    time_remaining = threshold - elapsed
    
    return {
        "incident_id": incident_id,
        "breach_predicted": time_remaining < 0,
        "time_remaining_seconds": float(time_remaining)
    }


def incident_sla_tracker(payload=None, **kwargs):
    if payload is not None and isinstance(payload, dict):
        return track_incident_sla(payload)
    if kwargs:
        return track_incident_sla(kwargs)
    return IncidentSLATracker()
