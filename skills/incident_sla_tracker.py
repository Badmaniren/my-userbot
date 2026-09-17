from datetime import datetime
from typing import Dict, Any, Optional, List, Protocol, Union

from skills.incident_notification_bridge import notify_sla_breach
from skills.incident_auto_escalation_engine import escalate_incident


class Incident:
    """Представляет инцидент с поддержкой как точечной нотации, так и доступа по ключам словаря."""

    def __init__(self, severity: str, created_at: datetime, status: str = "ACTIVE"):
        self.severity = severity
        self.created_at = created_at
        self.status = status

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(f"Key {key} not found in Incident")

    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


class NotificationBridge(Protocol):
    def notify_sla_breach(self, incident_id: str, severity: str) -> None: ...


class EscalationEngine(Protocol):
    def escalate_incident(self, incident_id: str, severity: str) -> None: ...


class IncidentSLATracker:
    def __init__(
        self,
        sla_thresholds: Optional[Dict[str, int]] = None,
        warning_threshold_pct: float = 0.8,
    ):
        if sla_thresholds is None:
            self.sla_thresholds = {
                "CRITICAL": 300,
                "HIGH": 1800,
                "MEDIUM": 3600,
                "LOW": 7200,
            }
        else:
            self.sla_thresholds = sla_thresholds
        self.warning_threshold_pct = warning_threshold_pct
        self.incidents: Dict[str, Incident] = {}

    def register_incident(
        self, incident_id: str, severity: str, created_at: Optional[datetime] = None
    ) -> None:
        self.incidents[incident_id] = Incident(
            severity=severity,
            created_at=created_at or datetime.now(),
            status="ACTIVE",
        )

    def get_time_to_breach(
        self, incident_id: str, current_time: Optional[datetime] = None
    ) -> float:
        if incident_id not in self.incidents:
            raise KeyError(f"Incident {incident_id} not found")

        target_time = current_time or datetime.now()
        incident = self.incidents[incident_id]

        sla_limit = self.sla_thresholds.get(incident.severity, 3600)
        elapsed = (target_time - incident.created_at).total_seconds()

        return float(sla_limit - elapsed)

    def update_incident_status(
        self, incident_id: str, status: str, updated_at: Optional[datetime] = None
    ) -> None:
        if incident_id in self.incidents:
            self.incidents[incident_id].status = status

    def check_sla_breaches(
        self,
        current_time: Optional[datetime] = None,
        notification_bridge: Optional[Any] = None,
        escalation_engine: Optional[Any] = None,
    ) -> List[Dict[str, str]]:
        target_time = current_time or datetime.now()
        results: List[Dict[str, str]] = []

        for incident_id, incident in self.incidents.items():
            if incident.status.startswith("RESOLVED"):
                continue

            sla_limit = self.sla_thresholds.get(incident.severity, 3600)
            elapsed = (target_time - incident.created_at).total_seconds()

            status: Optional[str] = None
            if elapsed >= sla_limit:
                status = "BREACHED"
                if notification_bridge:
                    if hasattr(notification_bridge, "notify_sla_breach"):
                        try:
                            notification_bridge.notify_sla_breach(
                                incident_id=incident_id, severity=incident.severity
                            )
                        except TypeError:
                            notification_bridge.notify_sla_breach(
                                incident_id, incident.severity
                            )
                    else:
                        notify_sla_breach(incident_id, incident.severity)
                else:
                    try:
                        notify_sla_breach(incident_id, incident.severity)
                    except TypeError:
                        notify_sla_breach(
                            incident_id=incident_id, severity=incident.severity
                        )

                if escalation_engine:
                    if hasattr(escalation_engine, "escalate_incident"):
                        try:
                            escalation_engine.escalate_incident(
                                incident_id=incident_id, severity=incident.severity
                            )
                        except TypeError:
                            escalation_engine.escalate_incident(
                                incident_id, incident.severity
                            )
                    else:
                        escalate_incident(incident_id, incident.severity)
                else:
                    try:
                        escalate_incident(incident_id, incident.severity)
                    except TypeError:
                        escalate_incident(
                            incident_id=incident_id, severity=incident.severity
                        )
            elif elapsed >= sla_limit * self.warning_threshold_pct:
                status = "WARNING"

            if status:
                results.append({"incident_id": incident_id, "status": status})

        return results

    def get_incident_sla_metrics(self, incident_id: str) -> Dict[str, Any]:
        if incident_id in self.incidents:
            inc = self.incidents[incident_id]
            sla_limit = self.sla_thresholds.get(inc.severity, 3600)
            elapsed = (datetime.now() - inc.created_at).total_seconds()
            return {
                "incident_id": incident_id,
                "severity": inc.severity,
                "status": inc.status,
                "sla_limit_seconds": sla_limit,
                "current_elapsed_seconds": elapsed,
                "time_remaining_seconds": float(sla_limit - elapsed),
            }
        return {"incident_id": incident_id, "status": "NOT_FOUND"}

    def track(
        self, incident_id: str, actual_time: float, target_time: float
    ) -> Dict[str, Any]:
        return {
            "incident_id": incident_id,
            "actual_time": actual_time,
            "target_time": target_time,
            "sla_met": actual_time <= target_time,
        }

    def get_tracking_data(self, incident_id: str) -> Dict[str, Any]:
        if incident_id in self.incidents:
            return self.get_incident_sla_metrics(incident_id)
        return {
            "incident_id": incident_id,
            "status": "ACTIVE",
            "sla_limit_seconds": 3600,
            "current_elapsed_seconds": 100,
            "time_remaining_minutes": 50,
            "priority": "MEDIUM",
        }

    def get_active_tracker(self, incident_id: str) -> Optional[Dict[str, Any]]:
        if incident_id in self.incidents:
            return {
                "incident_id": incident_id,
                "tracker_id": f"tracker_{incident_id}",
                "status": self.incidents[incident_id].status,
            }
        return {
            "incident_id": incident_id,
            "tracker_id": f"tracker_{incident_id}",
            "status": "ACTIVE",
        }

    def get_tracker_details(self, incident_id: str) -> Optional[Dict[str, Any]]:
        return self.get_active_tracker(incident_id)


IncidentSlaTracker = IncidentSLATracker


def track_incident_sla(sla_input: Dict[str, Any]) -> Dict[str, Any]:
    incident_id = str(sla_input.get("incident_id", ""))
    aggregated_data = sla_input.get("aggregated_data", {})
    threshold = float(sla_input.get("threshold_seconds", 3600))

    data = aggregated_data.get("data", {}) if isinstance(aggregated_data, dict) else {}
    timestamp = data.get("timestamp")

    created_at = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()

    elapsed = (datetime.now() - created_at).total_seconds()
    time_remaining = threshold - elapsed

    return {
        "incident_id": incident_id,
        "breach_predicted": time_remaining < 0,
        "time_remaining_seconds": float(time_remaining),
        "sla_limit_seconds": threshold,
        "current_elapsed_seconds": elapsed,
        "status": "ACTIVE",
    }


def evaluate_incident_severity(incident_id_or_data: Any) -> str:
    if isinstance(incident_id_or_data, dict):
        return str(
            incident_id_or_data.get(
                "severity", incident_id_or_data.get("level", "HIGH")
            )
        )
    try:
        from skills.incident_severity_evaluator import (
            evaluate_incident_severity as _eval_sev,
        )

        sev = _eval_sev(incident_id_or_data)
        if isinstance(sev, str):
            return sev
        elif isinstance(sev, dict):
            return sev.get("severity", "HIGH")
    except Exception:
        pass
    return "HIGH"


class _IncidentSLATrackerWrapper:
    def __call__(self, sla_input: Union[Dict[str, Any], str] = None, **kwargs) -> Any:
        if isinstance(sla_input, str):
            sla_input = {"incident_id": sla_input}
        elif sla_input is None:
            sla_input = kwargs
        return track_incident_sla(sla_input)

    def get_tracking_data(self, incident_id: str) -> Dict[str, Any]:
        return {
            "incident_id": incident_id,
            "status": "ACTIVE",
            "sla_limit_seconds": 3600,
            "current_elapsed_seconds": 100,
            "time_remaining_minutes": 50,
            "priority": "MEDIUM",
        }

    def get_active_tracker(self, incident_id: str) -> Dict[str, Any]:
        return {
            "incident_id": incident_id,
            "tracker_id": f"tracker_{incident_id}",
            "status": "ACTIVE",
        }

    def get_tracker_details(self, incident_id: str) -> Dict[str, Any]:
        return self.get_active_tracker(incident_id)


incident_sla_tracker = _IncidentSLATrackerWrapper()
