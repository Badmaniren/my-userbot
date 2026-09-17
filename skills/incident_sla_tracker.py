from datetime import datetime
from typing import Dict, Any, Optional, Union

# Import dependencies
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

# Attributes for unit test mocking
incident_notification_bridge = None
incident_auto_escalation_engine = None

DEFAULT_SLA_THRESHOLDS = {
    "CRITICAL": 300,
    "HIGH": 1800,
    "MEDIUM": 3600,
    "LOW": 7200,
}


class IncidentSLATracker:
    def __init__(
        self,
        sla_thresholds: Optional[Dict[str, int]] = None,
        warning_threshold_pct: float = 0.8,
    ):
        self.sla_thresholds = sla_thresholds if sla_thresholds is not None else dict(DEFAULT_SLA_THRESHOLDS)
        self.warning_threshold_pct = warning_threshold_pct
        self.incidents: Dict[str, Dict[str, Any]] = {}

    def register_incident(
        self,
        incident_id: str,
        severity: str = "HIGH",
        created_at: Optional[datetime] = None,
    ) -> None:
        created = created_at or datetime.now()
        self.incidents[incident_id] = {
            "incident_id": incident_id,
            "severity": severity,
            "created_at": created,
            "status": "ACTIVE",
            "updated_at": created,
        }

    def get_time_to_breach(
        self, incident_id: str, current_time: Optional[datetime] = None
    ) -> float:
        if incident_id not in self.incidents:
            raise KeyError(f"Incident {incident_id} not found")

        target_time = current_time or datetime.now()
        incident = self.incidents[incident_id]

        sla_limit = self.sla_thresholds.get(incident["severity"], 3600)
        elapsed = (target_time - incident["created_at"]).total_seconds()

        return float(sla_limit - elapsed)

    def update_incident_status(
        self,
        incident_id: str,
        status: str,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if incident_id in self.incidents:
            self.incidents[incident_id]["status"] = status
            self.incidents[incident_id]["updated_at"] = updated_at or datetime.now()

    def check_sla_breaches(
        self,
        current_time: Optional[datetime] = None,
        notification_bridge: Optional[Any] = None,
        escalation_engine: Optional[Any] = None,
    ) -> list:
        target_time = current_time or datetime.now()
        results = []

        notif_bridge = notification_bridge or incident_notification_bridge
        esc_engine = escalation_engine or incident_auto_escalation_engine

        for incident_id, incident in self.incidents.items():
            if incident["status"].startswith("RESOLVED"):
                continue

            severity = incident["severity"]
            sla_limit = self.sla_thresholds.get(severity, 3600)
            elapsed = (target_time - incident["created_at"]).total_seconds()

            status = None
            if elapsed >= sla_limit:
                status = "BREACHED"
                if notif_bridge and hasattr(notif_bridge, "notify_sla_breach"):
                    notif_bridge.notify_sla_breach(
                        incident_id=incident_id, severity=severity
                    )
                if esc_engine and hasattr(esc_engine, "escalate_incident"):
                    esc_engine.escalate_incident(
                        incident_id=incident_id, severity=severity
                    )
            elif elapsed >= sla_limit * self.warning_threshold_pct:
                status = "WARNING"

            if status:
                results.append(
                    {
                        "incident_id": incident_id,
                        "status": status,
                    }
                )

        return results

    def get_incident_sla_metrics(
        self, incident_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if incident_id:
            if incident_id not in self.incidents:
                return {}
            inc = self.incidents[incident_id]
            time_to_breach = self.get_time_to_breach(incident_id)
            return {
                "incident_id": incident_id,
                "severity": inc["severity"],
                "status": inc["status"],
                "time_to_breach": time_to_breach,
                "is_breached": time_to_breach <= 0,
            }

        total = len(self.incidents)
        active = sum(1 for inc in self.incidents.values() if inc["status"] == "ACTIVE")
        breached = sum(1 for inc_id in self.incidents if self.get_time_to_breach(inc_id) <= 0)
        return {
            "total_incidents": total,
            "active_incidents": active,
            "breached_incidents": breached,
            "incidents": self.incidents,
        }

    def track(
        self,
        incident_id_or_data: Any,
        severity: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        if isinstance(incident_id_or_data, dict):
            inc_id = incident_id_or_data.get("incident_id", "INC-UNKNOWN")
            sev = (
                severity
                or incident_id_or_data.get("severity")
                or incident_id_or_data.get("severity_level")
                or "HIGH"
            )
            c_at = created_at or incident_id_or_data.get("created_at")
            if isinstance(c_at, (int, float)):
                c_at = datetime.fromtimestamp(c_at)
            elif not isinstance(c_at, datetime):
                c_at = datetime.now()
        else:
            inc_id = str(incident_id_or_data)
            sev = severity or "HIGH"
            c_at = created_at or datetime.now()

        self.register_incident(inc_id, sev, c_at)
        return self.get_incident_sla_metrics(inc_id)

    def get_tracking_data(
        self, incident_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if incident_id:
            return self.incidents.get(incident_id, {})
        return dict(self.incidents)

    def get_active_tracker(self) -> "IncidentSLATracker":
        return self

    def get_tracker_details(
        self, incident_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return self.get_incident_sla_metrics(incident_id)


# Alias
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
        "time_remaining_seconds": float(time_remaining),
    }


def incident_sla_tracker(
    sla_input: Optional[Any] = None, **kwargs
) -> Any:
    if isinstance(sla_input, dict):
        return track_incident_sla(sla_input)
    if sla_input is None and kwargs:
        return track_incident_sla(kwargs)
    return IncidentSLATracker(sla_thresholds=sla_input, **kwargs)
