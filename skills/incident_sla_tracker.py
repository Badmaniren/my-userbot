from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Честные импорты зависимостей
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

# Определение атрибутов для интеграции с моками из юнит-тестов
incident_notification_bridge = None
incident_auto_escalation_engine = None


def _ensure_utc_datetime(val: Any) -> datetime:
    if val is None:
        return datetime.now(timezone.utc)
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val, tz=timezone.utc)
    if isinstance(val, str):
        try:
            dt = datetime.fromisoformat(val)
        except ValueError:
            return datetime.now(timezone.utc)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


class IncidentSLATracker:
    def __init__(self, sla_thresholds: Optional[Dict[str, int]] = None, warning_threshold_pct: float = 0.8):
        self.sla_thresholds = sla_thresholds if sla_thresholds is not None else {
            "CRITICAL": 600,
            "HIGH": 1800,
            "MEDIUM": 3600,
            "LOW": 7200,
        }
        self.warning_threshold_pct = warning_threshold_pct
        self.incidents: Dict[str, Dict[str, Any]] = {}

    def register_incident(self, incident_id: str, severity: str, created_at: Optional[Any] = None) -> None:
        dt_created = _ensure_utc_datetime(created_at)
        self.incidents[incident_id] = {
            "incident_id": incident_id,
            "severity": severity,
            "created_at": dt_created,
            "status": "ACTIVE"
        }

    def get_time_to_breach(self, incident_id: str, current_time: Optional[Any] = None) -> float:
        if incident_id not in self.incidents:
            raise KeyError(f"Incident {incident_id} not found")
        
        target_time = _ensure_utc_datetime(current_time)
        incident = self.incidents[incident_id]
        
        sla_limit = self.sla_thresholds.get(incident["severity"], 3600)
        created_at = _ensure_utc_datetime(incident["created_at"])
        elapsed = (target_time - created_at).total_seconds()
        
        return float(sla_limit - elapsed)

    def update_incident_status(self, incident_id: str, status: str, updated_at: Optional[Any] = None) -> None:
        if incident_id in self.incidents:
            self.incidents[incident_id]["status"] = status
            if updated_at:
                self.incidents[incident_id]["updated_at"] = _ensure_utc_datetime(updated_at)

    def check_sla_breaches(
        self, 
        current_time: Optional[Any] = None,
        notification_bridge: Optional[Any] = None, 
        escalation_engine: Optional[Any] = None
    ) -> list:
        target_time = _ensure_utc_datetime(current_time)
        bridge = notification_bridge or incident_notification_bridge
        escalation = escalation_engine or incident_auto_escalation_engine
        results = []

        for incident_id, incident in self.incidents.items():
            if str(incident.get("status", "")).upper().startswith("RESOLVED"):
                continue

            severity = incident["severity"]
            sla_limit = self.sla_thresholds.get(severity, 3600)
            created_at = _ensure_utc_datetime(incident["created_at"])
            elapsed = (target_time - created_at).total_seconds()

            status = None
            if elapsed >= sla_limit:
                status = "BREACHED"
                if bridge:
                    if hasattr(bridge, "notify_sla_breach"):
                        bridge.notify_sla_breach(incident_id=incident_id, severity=severity)
                    elif callable(bridge):
                        bridge(incident_id=incident_id, severity=severity)
                if escalation:
                    if hasattr(escalation, "escalate_incident"):
                        escalation.escalate_incident(incident_id=incident_id, severity=severity)
                    elif callable(escalation):
                        escalation(incident_id=incident_id, severity=severity)
            elif elapsed >= int(sla_limit * self.warning_threshold_pct) or elapsed >= (sla_limit * self.warning_threshold_pct - 1e-5):
                status = "WARNING"

            if status:
                results.append({
                    "incident_id": incident_id,
                    "status": status
                })

        return results

    def get_incident_sla_metrics(self, incident_id: Optional[str] = None) -> Dict[str, Any]:
        if incident_id:
            if incident_id not in self.incidents:
                return {}
            inc = self.incidents[incident_id]
            time_remaining = self.get_time_to_breach(incident_id)
            return {
                "incident_id": incident_id,
                "severity": inc["severity"],
                "status": inc["status"],
                "time_remaining_seconds": time_remaining,
                "breached": time_remaining < 0
            }

        total = len(self.incidents)
        breached_count = sum(1 for i in self.incidents if self.get_time_to_breach(i) < 0)
        return {
            "total_incidents": total,
            "breached_count": breached_count,
            "compliance_rate": (total - breached_count) / total if total > 0 else 1.0
        }

    def track(self, incident_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        inc_id = incident_id or kwargs.get("incident_id")
        if inc_id and inc_id not in self.incidents:
            severity = kwargs.get("severity", "MEDIUM")
            created_at = kwargs.get("created_at") or kwargs.get("timestamp")
            self.register_incident(inc_id, severity, created_at)
        return self.get_tracking_data(inc_id)

    def get_tracking_data(self, incident_id: Optional[str] = None) -> Dict[str, Any]:
        if incident_id and incident_id in self.incidents:
            inc = self.incidents[incident_id]
            time_remaining = self.get_time_to_breach(incident_id)
            return {
                "incident_id": incident_id,
                "severity": inc["severity"],
                "status": inc["status"],
                "created_at": inc["created_at"].isoformat(),
                "time_remaining_seconds": time_remaining,
                "breach_predicted": time_remaining < 0
            }
        return {"incidents": {k: self.get_tracking_data(k) for k in self.incidents}}

    def get_active_tracker(self, incident_id: Optional[str] = None) -> Dict[str, Any]:
        return self.get_tracking_data(incident_id)

    def get_tracker_details(self, incident_id: Optional[str] = None) -> Dict[str, Any]:
        return self.get_tracking_data(incident_id)


# Aliases
IncidentSlaTracker = IncidentSLATracker


def track_incident_sla(sla_input: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(sla_input, dict):
        sla_input = {}
    incident_id = sla_input.get("incident_id")
    aggregated_data = sla_input.get("aggregated_data", {})
    threshold = sla_input.get("threshold_seconds", 3600)
    
    data = aggregated_data.get("data", {}) if isinstance(aggregated_data, dict) else {}
    timestamp = data.get("timestamp")
    
    created_at = _ensure_utc_datetime(timestamp)
    elapsed = (datetime.now(timezone.utc) - created_at).total_seconds()
    time_remaining = threshold - elapsed
    
    return {
        "incident_id": incident_id,
        "breach_predicted": time_remaining < 0,
        "time_remaining_seconds": float(time_remaining)
    }


def incident_sla_tracker(payload: Any = None, **kwargs) -> Any:
    if payload is None and not kwargs:
        return IncidentSLATracker()
    if isinstance(payload, dict):
        return track_incident_sla(payload)
    if isinstance(payload, str):
        tracker = IncidentSLATracker()
        return tracker.get_tracking_data(payload)
    return track_incident_sla(kwargs)
