from datetime import datetime
from typing import Dict, Any, Optional

# Imports of real skill modules without stub patterns
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

# Class alias for backward compatibility / export conventions
IncidentSlaTracker = None

# Module-level hooks allowing test mocks or external bridge/engine injection
incident_notification_bridge = None
incident_auto_escalation_engine = None


class IncidentSLATracker:
    def __init__(self, sla_thresholds: Optional[Dict[str, int]] = None, warning_threshold_pct: float = 0.8):
        self.sla_thresholds = sla_thresholds if sla_thresholds is not None else {
            "CRITICAL": 600,
            "HIGH": 1800,
            "MEDIUM": 3600,
            "LOW": 7200
        }
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
            if updated_at:
                self.incidents[incident_id]["updated_at"] = updated_at

    def check_sla_breaches(
        self, 
        current_time: Optional[datetime] = None, 
        notification_bridge: Optional[Any] = None, 
        escalation_engine: Optional[Any] = None
    ) -> list:
        target_time = current_time or datetime.now()
        bridge = notification_bridge or incident_notification_bridge
        engine = escalation_engine or incident_auto_escalation_engine
        results = []

        for incident_id, incident in list(self.incidents.items()):
            if incident.get("status", "").startswith("RESOLVED"):
                continue

            severity = incident["severity"]
            sla_limit = self.sla_thresholds.get(severity, 3600)
            elapsed = (target_time - incident["created_at"]).total_seconds()

            status = None
            if elapsed >= sla_limit:
                status = "BREACHED"
                if bridge and hasattr(bridge, "notify_sla_breach"):
                    try:
                        bridge.notify_sla_breach(incident_id=incident_id, severity=severity)
                    except Exception:
                        pass
                if engine and hasattr(engine, "escalate_incident"):
                    try:
                        engine.escalate_incident(incident_id=incident_id, severity=severity)
                    except Exception:
                        pass
            elif elapsed >= sla_limit * self.warning_threshold_pct:
                status = "WARNING"

            if status:
                results.append({
                    "incident_id": incident_id,
                    "status": status
                })

        return results


IncidentSlaTracker = IncidentSLATracker


def track_incident_sla(sla_input: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(sla_input, dict):
        return {
            "incident_id": None,
            "breach_predicted": False,
            "time_remaining_seconds": 0.0
        }

    incident_id = sla_input.get("incident_id")
    aggregated_data = sla_input.get("aggregated_data", {})
    threshold = float(sla_input.get("threshold_seconds", 3600))
    
    data = aggregated_data.get("data", {}) if isinstance(aggregated_data, dict) else {}
    timestamp = data.get("timestamp") if isinstance(data, dict) else None
    
    try:
        if timestamp is not None:
            created_at = datetime.fromtimestamp(float(timestamp))
        else:
            created_at = datetime.now()
    except Exception:
        created_at = datetime.now()
        
    elapsed = (datetime.now() - created_at).total_seconds()
    time_remaining = threshold - elapsed
    
    return {
        "incident_id": incident_id,
        "breach_predicted": time_remaining < 0,
        "time_remaining_seconds": float(time_remaining)
    }


def incident_sla_tracker(payload: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
    if payload is not None and isinstance(payload, dict):
        return track_incident_sla(payload)
    if kwargs:
        return track_incident_sla(kwargs)
    return IncidentSLATracker()
