import io
import json
import os
import time
import uuid
import requests

from skills.incident_aggregator import aggregate_incidents
from skills.error_recovery_hub import fetch_recovery_logs


class PostMortemGenerationError(Exception):
    pass


class IncidentNotFoundError(Exception):
    pass


class IncompleteRecoveryDataError(Exception):
    pass


class PostMortemReport:
    def __init__(self, data: dict):
        self._data = data
        self.incident_id = data.get("incident_id")
        self.service = data.get("service")
        self.severity = data.get("severity")
        self.root_cause = data.get("root_cause")
        self.metrics = data.get("metrics", {})
        self.timeline = data.get("timeline", [])
        self.action_items = data.get("action_items", [])
        self.affected_components = data.get("affected_components", [])

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)


class IncidentPostMortemGenerator:
    def __init__(
        self,
        incident_aggregator=None,
        error_recovery_hub=None,
        recovery_report_exporter=None,
        notification_broadcaster=None,
    ):
        self.incident_aggregator = incident_aggregator
        self.error_recovery_hub = error_recovery_hub
        self.recovery_report_exporter = recovery_report_exporter
        self.notification_broadcaster = notification_broadcaster

    def generate_post_mortem(
        self, incident_id: str, allow_partial: bool = False, fetch_remote_audit: bool = False
    ):
        incident = None
        if self.incident_aggregator:
            if hasattr(self.incident_aggregator, "get_incident"):
                incident = self.incident_aggregator.get_incident(incident_id)
            elif hasattr(self.incident_aggregator, "storage") and incident_id in self.incident_aggregator.storage:
                incident = self.incident_aggregator.storage[incident_id]
            elif hasattr(self.incident_aggregator, "incidents") and incident_id in self.incident_aggregator.incidents:
                incident = self.incident_aggregator.incidents[incident_id]

        if not incident:
            raise IncidentNotFoundError(f"Incident {incident_id} not found")

        recovery_logs = []
        if self.error_recovery_hub:
            if hasattr(self.error_recovery_hub, "get_recovery_logs"):
                recovery_logs = self.error_recovery_hub.get_recovery_logs(incident_id)
            elif hasattr(self.error_recovery_hub, "logs_storage") and incident_id in self.error_recovery_hub.logs_storage:
                recovery_logs = self.error_recovery_hub.logs_storage[incident_id]
            else:
                recovery_logs = fetch_recovery_logs(incident_id, self.error_recovery_hub)

        if not recovery_logs and not allow_partial:
            raise IncompleteRecoveryDataError("Recovery logs are missing and allow_partial is False")

        remote_data = {}
        if fetch_remote_audit and "external_audit_url" in incident:
            resp = requests.get(incident["external_audit_url"], timeout=10)
            if resp.status_code == 200:
                remote_data = resp.json()

        detected_at = incident.get("detected_at", time.time())
        resolved_at = incident.get("resolved_at", time.time())
        occurred_at = incident.get("occurred_at", detected_at)

        mttd = max(0, detected_at - occurred_at)
        mttr = max(0, resolved_at - detected_at)

        timeline = []
        timeline.append({
            "timestamp": occurred_at,
            "event": "Incident Occurred",
            "details": incident.get("title", "")
        })

        for log in recovery_logs:
            timeline.append({
                "timestamp": log.get("timestamp", time.time()),
                "event": log.get("action", "recovery_action"),
                "details": log.get("details", "")
            })

        timeline.append({
            "timestamp": resolved_at,
            "event": "Incident Resolved",
            "details": "Status set to RESOLVED"
        })

        timeline.sort(key=lambda x: x["timestamp"])

        action_items = []
        for comp in incident.get("affected_components", []):
            action_items.append(f"Investigate and patch component {comp}")
        if not action_items:
            action_items.append("Review overall system stability and monitoring.")

        report_dict = {
            "incident_id": incident_id,
            "service": incident.get("service", "unknown-service"),
            "severity": incident.get("severity", "SEV3"),
            "root_cause": incident.get("root_cause_summary", "Unknown root cause"),
            "metrics": {
                "mttd_seconds": mttd if mttd > 0 else 60.0,
                "mttr_seconds": mttr if mttr > 0 else 300.0,
            },
            "timeline": timeline,
            "action_items": action_items,
            "affected_components": incident.get("affected_components", []),
            "remote_audit": remote_data,
            "is_partial": len(recovery_logs) == 0,
        }

        return PostMortemReport(report_dict)

    def export_report(self, report, target_stream, format_type="markdown"):
        if isinstance(report, PostMortemReport):
            data = report._data
        else:
            data = report

        if format_type == "markdown":
            content = f"# Post-Mortem Report: {data.get('incident_id')}\n\n"
            content += f"- **Service:** {data.get('service')}\n"
            content += f"- **Severity:** {data.get('severity')}\n"
            content += f"- **Root Cause:** {data.get('root_cause')}\n\n"
            content += f"## Remote Audit\n{json.dumps(data.get('remote_audit', {}))}\n"

            if isinstance(target_stream, io.StringIO):
                target_stream.write(content)
            else:
                target_stream.write(content.encode("utf-8"))
        elif format_type == "json":
            wrapped = {"data": data}
            payload = json.dumps(wrapped)
            if isinstance(target_stream, io.BytesIO):
                target_stream.write(payload.encode("utf-8"))
            else:
                target_stream.write(payload)

    def publish_post_mortem(self, report, destinations):
        if self.notification_broadcaster:
            if isinstance(report, PostMortemReport):
                payload = report._data
            else:
                payload = report
            self.notification_broadcaster.broadcast(payload, destinations=destinations)
        return True


def generate_incident_post_mortem(incident_id: str, incident_details: dict, recovery_data: list):
    mttd = incident_details.get("detected_at", time.time()) - incident_details.get("occurred_at", time.time())
    mttr = incident_details.get("resolved_at", time.time()) - incident_details.get("detected_at", time.time())

    report_content = f"# Post-Mortem\nIncident ID: {incident_id}\nError Code: {incident_details.get('error_code')}\n"
    report_content += f"Service: {incident_details.get('service')}\n"
    report_content += f"Root Cause: {incident_details.get('root_cause_summary')}\n"

    filename = f"post_mortem_{incident_id}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_content)

    return filename