import json
import uuid
import os

from skills.incident_sla_tracker import IncidentSLATracker
from skills.incident_sla_breach_predictor import incident_sla_breach_predictor

class IncidentSLAAuditReporter:
    def __init__(self, sla_tracker=None, sla_predictor=None):
        self.sla_tracker = sla_tracker
        self.sla_predictor = sla_predictor

    def generate_audit_report(self, period_id=None, audit_id=None, incident_id=None, tracker_data=None, predictor_data=None, format="json"):
        if tracker_data is not None and predictor_data is not None:
            compliance_rate = tracker_data.get("compliance_score", 100.0)
            predicted_risk = predictor_data.get("risk_score", 0.0)
            vulnerabilities = []

            return {
                "report_id": str(uuid.uuid4()),
                "period_id": period_id,
                "incident_id": incident_id,
                "compliance_rate": compliance_rate,
                "predicted_risk": predicted_risk,
                "vulnerabilities": vulnerabilities,
                "official_audit": True
            }

        if self.sla_tracker is not None:
            metrics = self.sla_tracker.get_metrics(period_id=period_id)
        else:
            metrics = {}

        if self.sla_predictor is not None:
            risks = self.sla_predictor.evaluate_risks(period_id=period_id)
        else:
            risks = {}

        return {
            "period_id": metrics.get("audit_period", period_id),
            "compliance_rate": metrics.get("overall_compliance", 100.0),
            "predicted_risk": risks.get("risk_score", 0.0),
            "vulnerabilities": risks.get("vulnerable_services", [])
        }

    def export_report(self, target_path: str, format_type: str = "json") -> str:
        report_data = self.generate_audit_report()
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f)
        return target_path


def incident_sla_audit_reporter(payload: dict) -> dict:
    reporter = IncidentSLAAuditReporter()
    report = reporter.generate_audit_report(
        audit_id=payload.get("audit_id"),
        incident_id=payload.get("incident_id"),
        tracker_data=payload.get("tracker_data"),
        predictor_data=payload.get("predictor_data"),
        format=payload.get("format", "json")
    )

    if payload.get("format") == "json" and "file_path" not in report:
        file_path = f"audit_report_{uuid.uuid4().hex}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f)
        report["file_path"] = file_path

    return report