from datetime import datetime
from typing import Dict, Any, Optional, List

from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

incident_notification_bridge = None
incident_auto_escalation_engine = None


class IncidentSLATracker:
    def __init__(self, sla_thresholds: Dict[str, int] = None, warning_threshold_pct: float = 0.8):
        self.sla_thresholds = sla_thresholds if sla_thresholds is not None else {
            "CRITICAL": 900,
            "HIGH": 3600,
            "MEDIUM": 14400,
            "LOW": 86400
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
    ) -> List[Dict[str, Any]]:
        target_time = current_time or datetime.now()
        results = []

        nb = notification_bridge or incident_notification_bridge
        ee = escalation_engine or incident_auto_escalation_engine

        for incident_id, incident in self.incidents.items():
            if incident["status"].startswith("RESOLVED"):
                continue

            severity = incident["severity"]
            sla_limit = self.sla_thresholds.get(severity, 3600)
            elapsed = (target_time - incident["created_at"]).total_seconds()

            status = None
            if elapsed >= sla_limit:
                status = "BREACHED"
                if nb:
                    if hasattr(nb, "notify_sla_breach"):
                        nb.notify_sla_breach(incident_id=incident_id, severity=severity)
                    elif callable(nb):
                        nb(incident_id=incident_id, severity=severity)
                if ee:
                    if hasattr(ee, "escalate_incident"):
                        ee.escalate_incident(incident_id=incident_id, severity=severity)
                    elif callable(ee):
                        ee(incident_id=incident_id, severity=severity)
            elif elapsed >= sla_limit * self.warning_threshold_pct:
                status = "WARNING"

            if status:
                results.append({
                    "incident_id": incident_id,
                    "status": status
                })

        return results

    def get_incident_sla_metrics(self, incident_id: str) -> Dict[str, Any]:
        if incident_id not in self.incidents:
            return {
                "incident_id": incident_id,
                "status": "UNKNOWN",
                "time_to_breach": 0.0,
                "is_breached": False
            }
        inc = self.incidents[incident_id]
        ttb = self.get_time_to_breach(incident_id)
        return {
            "incident_id": incident_id,
            "severity": inc.get("severity"),
            "status": inc.get("status"),
            "created_at": inc.get("created_at"),
            "time_to_breach": ttb,
            "is_breached": ttb < 0
        }

    def track(self, incident_id: str, severity: str = "HIGH", created_at: Optional[datetime] = None) -> Dict[str, Any]:
        created_at = created_at or datetime.now()
        self.register_incident(incident_id, severity, created_at)
        return self.get_incident_sla_metrics(incident_id)

    def get_tracking_data(self, incident_id: str) -> Dict[str, Any]:
        return self.get_incident_sla_metrics(incident_id)

    def get_active_tracker(self, incident_id: Optional[str] = None) -> Dict[str, Any]:
        if incident_id and incident_id in self.incidents:
            return self.get_incident_sla_metrics(incident_id)
        return {"active_incidents": len(self.incidents), "incidents": self.incidents}

    def get_tracker_details(self, incident_id: str) -> Dict[str, Any]:
        return self.get_incident_sla_metrics(incident_id)


IncidentSlaTracker = IncidentSLATracker


def track_incident_sla(sla_input: Dict[str, Any]) -> Dict[str, Any]:
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


def incident_sla_tracker(payload: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    data = payload if isinstance(payload, dict) else kwargs
    if "incident_id" in data:
        return track_incident_sla(data)
    return {"status": "active", "tracked": True}
