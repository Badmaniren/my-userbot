import json
import os
from datetime import datetime
import requests

from skills.incident_sla_tracker import incident_sla_tracker
from skills.incident_sla_breach_predictor import incident_sla_breach_predictor
from skills.incident_sla_mitigation_planner import incident_sla_mitigation_planner

class ComplianceReportError(Exception):
    """Исключение для ошибок генерации отчетов о соответствии."""
    pass


class IncidentSlaComplianceReporter:
    def __init__(self, reporter_id: str, standard: str):
        self.reporter_id = reporter_id
        self.standard = standard

    def generate_audit_report(self, tracker_metrics: dict, breach_predictors: dict, mitigation_plans: list) -> dict:
        if not isinstance(tracker_metrics, dict) or "metric_id" not in tracker_metrics:
            raise ComplianceReportError("Invalid or corrupted tracker_metrics provided.")

        report = {
            "reporter_id": self.reporter_id,
            "standard": self.standard,
            "metrics": tracker_metrics,
            "predictors": breach_predictors,
            "mitigation_plans": mitigation_plans if isinstance(mitigation_plans, list) else [mitigation_plans],
            "generated_at": datetime.utcnow().isoformat()
        }
        return report

    def create_compliance_status_log(self, compliance_data: dict) -> str:
        log_prefix = compliance_data.get("log_prefix", "log")
        audit_passed = compliance_data.get("audit_passed", False)
        score = compliance_data.get("score", 0)
        timestamp = datetime.utcnow().isoformat()

        log_str = f"[{timestamp}] Prefix: {log_prefix} | Standard: {self.standard} | Passed: {audit_passed} | Score: {score}"
        return log_str

    def export_report_stream(self, report: dict, stream):
        content = json.dumps(report)
        stream.write(content.encode('utf-8'))

    def submit_report_governance(self, endpoint: str, payload: dict) -> dict:
        response = requests.post(endpoint, json=payload)
        return response.json()

    def submit_report_to_governance(self, endpoint: str, payload: dict) -> dict:
        return self.submit_report_governance(endpoint, payload)


def incident_sla_compliance_reporter(incident_id: str, tracker_metrics: dict, breach_predictors: dict, mitigation_plans: list):
    reporter = IncidentSlaComplianceReporter(
        reporter_id=incident_id,
        standard="ISO-9001"
    )

    report = reporter.generate_audit_report(
        tracker_metrics=tracker_metrics,
        breach_predictors=breach_predictors,
        mitigation_plans=mitigation_plans if isinstance(mitigation_plans, list) else [mitigation_plans]
    )

    report_file_path = f"audit_report_{incident_id}.log"
    content = json.dumps(report)
    f = open(report_file_path, "w")
    try:
        f.write(f"Incident ID: {incident_id}\n")
        f.write(content)
    finally:
        f.close()

    return report