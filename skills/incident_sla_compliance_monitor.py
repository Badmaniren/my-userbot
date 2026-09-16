from datetime import datetime
from typing import Dict, Any, Optional, Union
from skills import incident_sla_tracker, incident_sla_mitigation_planner


class IncidentSLAComplianceMonitor:
    def __init__(self, tracker=None, planner=None):
        self.tracker = tracker if tracker is not None else incident_sla_tracker
        self.planner = planner if planner is not None else incident_sla_mitigation_planner

    def monitor_compliance(self, incident_id: str, threshold_seconds: float) -> Dict[str, Any]:
        try:
            if hasattr(self.tracker, "get_status"):
                status = self.tracker.get_status(incident_id)
            elif hasattr(self.tracker, "track_incident_sla"):
                status = self.tracker.track_incident_sla({"incident_id": incident_id, "threshold_seconds": threshold_seconds})
            else:
                status = {"elapsed": 0.0}

            elapsed = status.get('elapsed', status.get('elapsed_seconds', 0.0))
            if elapsed > threshold_seconds:
                if hasattr(self.planner, "trigger_mitigation"):
                    self.planner.trigger_mitigation(incident_id)
                elif hasattr(self.planner, "plan_incident_sla_mitigation"):
                    self.planner.plan_incident_sla_mitigation(incident_id=incident_id)

                return {"status": "breached", "action": "mitigation_triggered"}
            return {"status": "compliant", "action": "none"}
        except Exception as e:
            raise RuntimeError(f"Compliance monitoring failed: {e}")


def monitor_incident_sla_compliance(
    incident_id: Optional[str] = None,
    tracker_data: Optional[Dict[str, Any]] = None,
    mitigation_data: Optional[Dict[str, Any]] = None,
    payload: Union[Dict[str, Any], str, None] = None,
    **kwargs: Any
) -> Dict[str, Any]:
    target_id = incident_id
    if isinstance(payload, str):
        target_id = payload
    elif isinstance(payload, dict):
        if not target_id:
            target_id = payload.get("incident_id")
        if not tracker_data:
            tracker_data = payload.get("tracker_data")
        if not mitigation_data:
            mitigation_data = payload.get("mitigation_data")

    if tracker_data is None:
        tracker_data = {}
    if mitigation_data is None:
        mitigation_data = {}

    status_str = "MONITORED_BREACH" if tracker_data.get("breach_detected", False) else "MONITORED_COMPLIANT"
    return {
        "incident_id": target_id,
        "status": status_str,
        "timestamp": datetime.utcnow().isoformat(),
        "tracker_data": tracker_data,
        "mitigation_data": mitigation_data
    }


incident_sla_compliance_monitor = IncidentSLAComplianceMonitor