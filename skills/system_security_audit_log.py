import hashlib
import json

from skills.incident_aggregator import incident_aggregator
from skills.system_health_audit_pipeline import system_health_audit_pipeline

class SystemSecurityAuditLog:
    def collect_event(self, event_id, severity, component, message):
        event_data = f"[{severity}] {component}: {message} (ID: {event_id})\n"
        with open("security_events.log", "a", encoding="utf-8") as f:
            f.write(event_data)
        return event_data

    def structure_logs(self, raw_entries):
        entries = []
        for entry in raw_entries:
            entries.append({
                "id": entry.get("id"),
                "code": entry.get("code"),
                "payload": entry.get("payload")
            })
        return {
            "total_processed": len(raw_entries),
            "entries": entries
        }

    def export_logs(self, export_format, destination_path):
        with open(destination_path, "w", encoding="utf-8") as f:
            f.write(f"EXPORT FORMAT: {export_format}\n")
        return True

    def filter_by_severity(self, dataset, target_severity):
        return [item for item in dataset if item.get("severity") == target_severity]

    def correlate_incidents(self, incident_stream, correlation_key):
        return [inc for inc in incident_stream if inc.get("correlation_id") == correlation_key]

    def verify_log_integrity(self, stream_obj, algorithm="sha256"):
        hasher = getattr(hashlib, algorithm)()
        stream_obj.seek(0)
        while True:
            chunk = stream_obj.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
        return hasher.hexdigest()

def system_security_audit_log(audit_payload):
    log_file = audit_payload.get("log_file")
    incident = audit_payload.get("incident", {})
    incident_id = incident.get("incident_id", "")

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(audit_payload, default=str) + "\n")

    return {"status": "logged", "incident_id": incident_id}