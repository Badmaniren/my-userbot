import hashlib
import os
from skills.incident_aggregator import IncidentAggregator
from skills.incident_trend_analyzer import IncidentTrendAnalyzer
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.recovery_report_exporter import RecoveryReportExporter


class IncidentSeverityEvaluator:
    def re_evaluate(self, incident_data, trend_data, recovery_data):
        impact = incident_data.get("impact_score", 0)
        recurrence = trend_data.get("recurrence_rate", 0)
        failed_attempts = recovery_data.get("failed_attempts", 0)

        if impact > 80 or recurrence > 0.9 or failed_attempts >= 2:
            return "CRITICAL"
        return incident_data.get("severity", "SEV-3")


class IncidentPostMortemGenerator:
    def __init__(self, incident_aggregator=None, incident_trend_analyzer=None, error_recovery_hub=None, recovery_report_exporter=None):
        self.aggregator = incident_aggregator or IncidentAggregator()
        self.trend_analyzer = incident_trend_analyzer or IncidentTrendAnalyzer()
        self.recovery_hub = error_recovery_hub or ErrorRecoveryHub()
        self.exporter = recovery_report_exporter or RecoveryReportExporter()

    def generate(self, incident_id, include_raw_telemetry=False):
        if hasattr(self.aggregator, "get_incident"):
            incident_data = self.aggregator.get_incident(incident_id)
        elif hasattr(self.aggregator, "storage") and incident_id in self.aggregator.storage:
            incident_data = self.aggregator.storage[incident_id]
        else:
            incident_data = {"incident_id": incident_id}

        trend_data = self.trend_analyzer.analyze_trends(incident_data)
        recovery_data = self.recovery_hub.get_recovery_history(incident_id)

        evaluator = IncidentSeverityEvaluator()
        final_severity = evaluator.re_evaluate(incident_data, trend_data, recovery_data)

        report_payload = {
            "incident_id": incident_id,
            "severity": incident_data.get("severity"),
            "final_severity": final_severity,
            "trends": trend_data,
            "recovery_actions": recovery_data
        }

        if include_raw_telemetry and "log_pointer" in incident_data:
            log_pointer = incident_data["log_pointer"]
            with open(log_pointer, "rb") as f:
                content = f.read()
                report_payload["telemetry_hash"] = hashlib.sha256(content).hexdigest()

        export_path = self.exporter.export(report_payload)
        report_payload["export_path"] = export_path

        return report_payload


def generate_incident_post_mortem(incident_id, aggregated_data, trend_data, recovery_history, output_path):
    error_code = aggregated_data.get("error_code", "UNKNOWN")
    severity = aggregated_data.get("severity", "UNKNOWN")
    description = aggregated_data.get("description", "")

    content = f"""# Incident Post-Mortem: {incident_id}
- **Error Code:** {error_code}
- **Severity Level:** {severity}
- **Description:** {description}

## Trends
{trend_data}

## Recovery History
{recovery_history}
"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path