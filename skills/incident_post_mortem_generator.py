import uuid
import json
import os

from skills.incident_aggregator import aggregate_incidents
from skills.error_recovery_hub import process_error_recovery
from skills.incident_severity_evaluator import evaluate_incident_severity


class IncidentPostMortemGenerator:
    def __init__(self):
        pass

    def _fetch_external_telemetry(self, incident_id):
        return {"cpu_spike": 0.5}

    def _analyze_recovery_timeline(self, recovery_events):
        if not recovery_events:
            return {
                "total_duration": 0,
                "failure_rate": 0.0,
                "events_analyzed": 0
            }

        total_duration = sum(
            e.get("timestamp_end", 0) - e.get("timestamp_start", 0)
            for e in recovery_events
        )
        failed_count = sum(1 for e in recovery_events if e.get("status") == "FAILED")
        failure_rate = failed_count / len(recovery_events)

        return {
            "total_duration": total_duration,
            "failure_rate": failure_rate,
            "events_analyzed": len(recovery_events)
        }

    def generate_post_mortem_summary(
        self, incident_id, severity, escalations, recoveries, log_file_path
    ):
        log_content = ""
        if log_file_path and os.path.exists(log_file_path):
            with open(log_file_path, "r", encoding="utf-8") as f:
                log_content = f.read()

        root_cause = "INSUFFICIENT_LOG_DATA" if not log_content.strip() else "ANALYZED_OK"

        self._fetch_external_telemetry(incident_id)

        return {
            "summary_id": uuid.uuid4().hex,
            "incident_id": incident_id,
            "severity": severity,
            "escalation_steps_count": len(escalations),
            "recovery_actions_count": len(recoveries),
            "root_cause_analysis": root_cause
        }

    def export_report(self, report_data, target_file_path, format="json"):
        if format != "json":
            raise ValueError(f"Unsupported format: {format}")

        with open(target_file_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        return True


def generate_incident_post_mortem(post_mortem_input):
    incident = post_mortem_input.get("incident", {})
    severity = post_mortem_input.get("severity", {})
    recovery = post_mortem_input.get("recovery", {})
    output_dir = post_mortem_input.get("output_dir", ".")

    incident_id = incident.get("id", str(uuid.uuid4()))
    severity_level = severity.get("severity", "LOW")

    generator = IncidentPostMortemGenerator()
    summary = generator.generate_post_mortem_summary(
        incident_id=incident_id,
        severity=severity_level,
        escalations=[],
        recoveries=[recovery] if recovery else [],
        log_file_path=""
    )

    report_data = {
        "report_id": summary["summary_id"],
        "incident_id": incident_id,
        "severity": severity_level,
        "incident": incident,
        "recovery": recovery,
        "summary": summary
    }

    os.makedirs(output_dir, exist_ok=True)
    target_file_path = os.path.join(output_dir, f"post_mortem_{incident_id}.json")
    generator.export_report(report_data, target_file_path, format="json")

    return report_data