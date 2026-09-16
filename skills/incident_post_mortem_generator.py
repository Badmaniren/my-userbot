import uuid
import json
import os
from skills.incident_aggregator import aggregate_incidents
from skills.incident_auto_recovery_dispatcher import trigger_recovery_dispatch, dispatch_recovery

try:
    from skills.incident_auto_escalation_engine import evaluate_escalation
except ImportError:
    pass

class IncidentPostMortemGenerator:
    def generate_report(self, escalation_data: dict, recovery_data: dict) -> dict:
        if not escalation_data or "incident_id" not in escalation_data or "severity" not in escalation_data:
            raise ValueError("Missing required escalation fields")

        report = {
            "post_mortem_id": uuid.uuid4().hex,
            "incident_id": escalation_data.get("incident_id"),
            "severity": escalation_data.get("severity"),
            "root_cause": recovery_data.get("root_cause", ""),
            "resolution_steps": recovery_data.get("resolution_steps", "")
        }
        return report

    def export_report(self, report_data: dict, file_path: str) -> bool:
        content = json.dumps(report_data, indent=4).encode('utf-8')
        with open(file_path, "wb") as f:
            f.write(content)
        return True

    def extract_metrics_from_telemetry(self, file_path: str) -> dict:
        metrics = {}
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            for line in content.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    metrics[key.strip()] = val.strip()
        return metrics

    def compile_full_post_mortem(self, escalation_data: dict, recovery_data: dict, telemetry_path: str) -> dict:
        report = self.generate_report(escalation_data, recovery_data)
        metrics = self.extract_metrics_from_telemetry(telemetry_path)
        report["telemetry_metrics"] = metrics
        return report

def generate_post_mortem(generation_payload: dict) -> dict:
    incident_id = generation_payload.get("incident_id")
    aggregation = generation_payload.get("aggregation", {})
    escalation = generation_payload.get("escalation", {})
    recovery = generation_payload.get("recovery", {})
    output_path = generation_payload.get("output_path", f"/tmp/post_mortem_{incident_id}.json")

    escalation_data = {
        "incident_id": incident_id,
        "severity": escalation.get("severity", "MEDIUM")
    }
    recovery_data = {
        "root_cause": recovery.get("root_cause", "Automatic recovery triggered"),
        "resolution_steps": recovery.get("action", "Restarted service")
    }

    generator = IncidentPostMortemGenerator()
    report = generator.generate_report(escalation_data, recovery_data)
    generator.export_report(report, output_path)

    return {
        "status": "success",
        "incident_id": incident_id,
        "report": report
    }