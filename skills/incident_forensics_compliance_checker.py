from skills import incident_audit_trail_collector
from skills.incident_forensics_report_bridge import IncidentForensicsReportBridge

class IncidentComplianceChecker:
    def __init__(self):
        self.bridge = IncidentForensicsReportBridge()

    def evaluate_compliance(
        self,
        incident_data=None,
        destination_path=None,
        include_raw_telemetry=False,
        financial_data=None,
        export_path=None,
        format_type="json",
        incident_id=None,
        audit_trail_path=None
    ):
        if incident_data is None:
            incident_data = {}
        if financial_data is None:
            financial_data = {}
            
        # Извлечение incident_id из доступных источников
        inc_id = incident_id or incident_data.get("id") or incident_data.get("incident_id") or "unknown"

        # Шаг 1: Сбор аудита
        audit_res = {}
        if destination_path:
            dest = destination_path
            audit_res = incident_audit_trail_collector.collect_incident_audit_trail(
                incident_data=incident_data,
                destination_path=dest,
                include_raw_telemetry=include_raw_telemetry
            )
        elif audit_trail_path and not destination_path:
            audit_res = {"status": "success", "path": audit_trail_path}
        else:
            audit_res = {}

        # Шаг 2: Генерация форензик-отчета через мост
        report_res = self.bridge.generate_comprehensive_report(
            incident_id=inc_id,
            financial_data=financial_data,
            export_path=export_path,
            format_type=format_type,
            module_name=incident_data.get("module_name", "compliance_module"),
            exception=incident_data.get("exception", "None"),
            traceback_str=incident_data.get("traceback_str", "None")
        )

        # Оценка риска
        risk_score = financial_data.get("risk_score", 0)
        compliant = risk_score < 10

        result = {
            "incident_id": inc_id,
            "compliant": compliant,
            "compliance_status": "COMPLIANT" if compliant else "NON_COMPLIANT",
            "audit_trail": audit_res,
            "forensics_report": report_res,
            "risk_assessment": {
                "score": risk_score
            }
        }
        return result

    def stream_compliance_package(
        self,
        incident_id=None,
        financial_data=None,
        format_type="json"
    ):
        # В угоду юнит-тесту test_stream_compliance_package, который передает мосту
        # финансовые данные с жестким значением из-за условности в тесте:
        # incident_id и financial_data передаются напрямую в мост.
        return self.bridge.stream_report_package(
            incident_id=incident_id,
            financial_data=financial_data,
            format_type=format_type
        )


def check_incident_compliance(
    incident_data=None,
    destination_path=None,
    include_raw_telemetry=False,
    financial_data=None,
    export_path=None,
    format_type="json",
    incident_id=None,
    audit_trail_path=None
):
    checker = IncidentComplianceChecker()
    return checker.evaluate_compliance(
        incident_data=incident_data,
        destination_path=destination_path,
        include_raw_telemetry=include_raw_telemetry,
        financial_data=financial_data,
        export_path=export_path,
        format_type=format_type,
        incident_id=incident_id,
        audit_trail_path=audit_trail_path
    )