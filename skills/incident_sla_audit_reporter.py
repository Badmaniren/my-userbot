import uuid
import json
import datetime
import sys
try:
    import requests
except ImportError:
    requests = None

from skills.incident_sla_tracker import IncidentSlaTracker
from skills import incident_sla_tracker as ist_module
from skills import incident_aggregator
from skills import incident_severity_evaluator


def incident_sla_audit_reporter(payload: dict) -> dict:
    """Функция для интеграционных тестов (функциональный вызов)."""
    incident_id = payload.get("incident_id")
    reporter = IncidentSlaAuditReporter()
    report = reporter.generate_audit_report(incident_id)

    # Дополняем ключами для интеграционных тестов
    report["audit_timestamp"] = datetime.datetime.utcnow().isoformat()
    report["sla_compliant"] = report.get("status") == "MET" or report.get("compliant", True)
    return report


class IncidentSlaAuditReporter:
    def __init__(self, audit_context=None):
        self.audit_context = audit_context

    def generate_audit_report(self, incident_id: str) -> dict:
        tracker = IncidentSlaTracker()
        metrics = tracker.get_incident_sla_metrics(incident_id)

        audit_id = uuid.uuid4().hex
        target_hours = metrics.get("target_hours", 1)
        actual_hours = metrics.get("actual_hours", 0)
        status = metrics.get("status", "MET")

        compliance_score = 100.0 if status == "MET" else max(0.0, 100.0 - (actual_hours - target_hours) * 10)

        report = {
            "audit_id": audit_id,
            "incident_id": incident_id,
            "client": metrics.get("client", "Unknown"),
            "target_hours": target_hours,
            "actual_hours": actual_hours,
            "status": status,
            "compliance_score": round(compliance_score, 2),
            "evaluated_by": f"auditor-{uuid.uuid4().hex[:6]}",
            "compliant": status == "MET",
            "deviation_factor": round(abs(actual_hours - target_hours) / (target_hours or 1), 2)
        }
        return report

    def export_report_stream(self, incident_id: str, stream) -> bool:
        report = self.generate_audit_report(incident_id)
        data_str = json.dumps(report)
        stream.write(data_str.encode('utf-8'))
        return True

    def batch_audit_compliance(self, incident_ids: list) -> dict:
        details = []
        compliant_count = 0

        for inc_id in incident_ids:
            rep = self.generate_audit_report(inc_id)
            details.append(rep)
            if rep.get("compliant", False) or rep.get("status") == "MET":
                compliant_count += 1

        total = len(incident_ids)
        compliance_rate = (compliant_count / total) * 100 if total > 0 else 0.0

        return {
            "total_evaluated": total,
            "compliance_rate": round(compliance_rate, 2),
            "details": details
        }