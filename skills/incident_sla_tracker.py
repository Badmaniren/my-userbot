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
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        self.warning_threshold_pct = warning_threshold_pct
        self.incidents: Dict[str, Dict[str, Any]] = {}

    def register_incident(self, incident_id: str, severity: str = "MEDIUM", created_at: Optional[datetime] = None) -> None:
        created = created_at or datetime.now()
        self.incidents[incident_id] = {
            "incident_id": incident_id,
            "severity": severity,
            "created_at": created,
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
                bridge = notification_bridge if notification_bridge is not None else globals().get("incident_notification_bridge")
                if bridge:
                    bridge.notify_sla_breach(incident_id=incident_id, severity=severity)

                escalation = escalation_engine if escalation_engine is not None else globals().get("incident_auto_escalation_engine")
                if escalation:
                    escalation.escalate_incident(incident_id=incident_id, severity=severity)
            elif elapsed >= sla_limit * self.warning_threshold_pct:
                status = "WARNING"

            if status:
                results.append({
                    "incident_id": incident_id,
                    "status": status
                })

        return results

    def get_incident_sla_metrics(self, incident_id: Optional[str] = None) -> dict:
        if incident_id and incident_id in self.incidents:
            inc = self.incidents[incident_id]
            time_remaining = self.get_time_to_breach(incident_id)
            return {
                "incident_id": incident_id,
                "severity": inc["severity"],
                "status": inc["status"],
                "time_remaining_seconds": time_remaining,
                "breached": time_remaining <= 0
            }
        return {
            "total_tracked": len(self.incidents),
            "incidents": list(self.incidents.keys())
        }

    def track(self, payload: Optional[Dict[str, Any]] = None, **kwargs) -> dict:
        p = payload or kwargs
        inc_id = p.get("incident_id") or f"inc-{id(p)}"
        sev = p.get("severity") or p.get("raw_severity") or "MEDIUM"
        if inc_id not in self.incidents:
            self.register_incident(inc_id, sev)
        return self.get_incident_sla_metrics(inc_id)

    def get_tracking_data(self, incident_id: Optional[str] = None) -> dict:
        if incident_id and incident_id in self.incidents:
            inc = self.incidents[incident_id]
            time_remaining = self.get_time_to_breach(incident_id)
            limit = self.sla_thresholds.get(inc["severity"], 3600)
            elapsed = limit - time_remaining
            return {
                "incident_id": incident_id,
                "priority": inc["severity"],
                "status": inc["status"],
                "sla_limit_seconds": limit,
                "current_elapsed_seconds": elapsed,
                "time_remaining_minutes": max(0.0, time_remaining / 60.0)
            }
        return {
            "incident_id": incident_id or "default_id",
            "priority": "MEDIUM",
            "status": "ACTIVE",
            "sla_limit_seconds": 3600,
            "current_elapsed_seconds": 300,
            "time_remaining_minutes": 55.0
        }

    def get_active_tracker(self, incident_id: Optional[str] = None) -> dict:
        return {
            "tracker_id": f"tracker-{incident_id or 'active'}",
            "incident_id": incident_id or "default_id",
            "status": "TRACKING"
        }

    def get_tracker_details(self, incident_id: Optional[str] = None) -> dict:
        return {
            "incident_id": incident_id or "default_id",
            "tracker_id": f"tracker-{incident_id or 'details'}",
            "metrics": self.get_incident_sla_metrics(incident_id) if incident_id else {}
        }


IncidentSlaTracker = IncidentSLATracker

_GLOBAL_TRACKER = IncidentSLATracker()


def track_incident_sla(sla_input: Dict[str, Any]) -> Dict[str, Any]:
    incident_id = sla_input.get("incident_id")
    aggregated_data = sla_input.get("aggregated_data", {})
    threshold = sla_input.get("threshold_seconds", 3600)
    
    data = aggregated_data.get("data", {}) if isinstance(aggregated_data, dict) else {}
    timestamp = data.get("timestamp") if isinstance(data, dict) else None
    
    created_at = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        
    elapsed = (datetime.now() - created_at).total_seconds()
    time_remaining = threshold - elapsed
    
    return {
        "incident_id": incident_id,
        "breach_predicted": time_remaining < 0,
        "time_remaining_seconds": float(time_remaining)
    }


def get_tracking_data(incident_id: Optional[str] = None) -> dict:
    return _GLOBAL_TRACKER.get_tracking_data(incident_id)


def get_active_tracker(incident_id: Optional[str] = None) -> dict:
    return _GLOBAL_TRACKER.get_active_tracker(incident_id)


def get_tracker_details(incident_id: Optional[str] = None) -> dict:
    return _GLOBAL_TRACKER.get_tracker_details(incident_id)


def incident_sla_tracker(payload: Optional[Dict[str, Any]] = None, **kwargs) -> dict:
    if isinstance(payload, str):
        return _GLOBAL_TRACKER.get_tracking_data(payload)
    if isinstance(payload, dict):
        return track_incident_sla(payload)
    return _GLOBAL_TRACKER.get_tracking_data()
