import os
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
        else:
            # Превращаем в изменяемый словарь, если передан несловарный объект
            incident_data = dict(incident_data)

        if financial_data is None:
            financial_data = {}
            
        # Извлечение incident_id из доступных источников с приоритетом аргумента incident_id, затем из incident_data
        inc_id = incident_id or incident_data.get("id") or incident_data.get("incident_id") or "unknown"

        # Гарантируем, что в самом incident_data будут проставлены оба ключа id и incident_id,
        # чтобы мост (или любые другие компоненты) надежно извлекли идентификатор.
        incident_data["id"] = inc_id
        incident_data["incident_id"] = inc_id

        # Шаг 1: Сбор аудита (корректная обработка, если destination_path является директорией)
        audit_res = {}
        if destination_path:
            dest = destination_path
            if os.path.isdir(dest):
                dest = os.path.join(dest, f"audit_{inc_id}.log")
            audit_res = incident_audit_trail_collector.collect_incident_audit_trail(
                incident_data=incident_data,
                destination_path=dest,
                include_raw_telemetry=include_raw_telemetry
            )
            if isinstance(audit_res, dict) and "path" not in audit_res:
                audit_res["path"] = dest
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