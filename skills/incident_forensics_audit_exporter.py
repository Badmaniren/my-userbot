import os
import json
import uuid
from skills import incident_audit_trail_collector
from skills import telemetry_audit_report_exporter as telemetry_audit_report_exporter_module


class IncidentForensicsAuditExporterException(Exception):
    """Исключение, выбрасываемое при ошибках экспорта форензик-аудита."""
    pass


def _resolve_exporter(exporter=None):
    if exporter is None:
        exporter = telemetry_audit_report_exporter_module
    if hasattr(exporter, "TelemetryAuditReportExporter"):
        cls = getattr(exporter, "TelemetryAuditReportExporter")
        if isinstance(cls, type):
            return cls()
    if isinstance(exporter, type):
        return exporter()
    return exporter


class IncidentForensicsAuditExporter:
    def __init__(self, audit_trail_collector=None, telemetry_audit_report_exporter=None):
        self.audit_trail_collector = audit_trail_collector or incident_audit_trail_collector
        self.telemetry_audit_report_exporter = (
            telemetry_audit_report_exporter
            if telemetry_audit_report_exporter is not None
            else telemetry_audit_report_exporter_module
        )

    def compose_forensics_evidence(
        self,
        incident_data,
        destination_path,
        include_raw_telemetry,
        telemetry_payload,
        epic_id,
        export_format,
        module_name,
        output_path
    ):
        try:
            audit_trail = self.audit_trail_collector.collect_incident_audit_trail(
                incident_data, destination_path, include_raw_telemetry
            )
        except Exception as e:
            raise IncidentForensicsAuditExporterException(str(e))

        incident_id = incident_data.get("id") or incident_data.get("incident_id")

        exporter = _resolve_exporter(self.telemetry_audit_report_exporter)

        if hasattr(exporter, "process_and_export_audit_report"):
            export_func = exporter.process_and_export_audit_report
        elif hasattr(exporter, "export_audit_report"):
            export_func = exporter.export_audit_report
        elif hasattr(exporter, "process_audit_report"):
            export_func = exporter.process_audit_report
        elif hasattr(exporter, "export_audit_and_recovery_report"):
            export_func = exporter.export_audit_and_recovery_report
        else:
            export_func = getattr(exporter, "process_audit_report")

        export_report = export_func(
            telemetry_payload=telemetry_payload,
            audit_data=audit_trail,
            epic_id=epic_id,
            incident_id=incident_id,
            module_name=module_name,
            output_path=output_path
        )

        return {
            "audit_trail": audit_trail,
            "export_report": export_report
        }

    def finalize_package_evidence(self, payload, output_path):
        exporter = _resolve_exporter(self.telemetry_audit_report_exporter)

        if hasattr(exporter, "finalize_epic_audit_export"):
            finalize_func = exporter.finalize_epic_audit_export
        elif hasattr(exporter, "finalize_audit_export"):
            finalize_func = exporter.finalize_audit_export
        else:
            finalize_func = getattr(exporter, "finalize_audit_export")

        return finalize_func(
            payload=payload,
            output_path=output_path
        )

    @staticmethod
    def start_new():
        return incident_audit_trail_collector.start_new()


def export_forensics_audit_package(
    incident_data,
    telemetry_payload,
    destination_path,
    epic_id,
    module_name
):
    collector = incident_audit_trail_collector

    incident_id = incident_data.get("incident_id") or incident_data.get("id")

    audit_trail = collector.collect_incident_audit_trail(
        incident_data, destination_path, True
    )

    exporter = _resolve_exporter(telemetry_audit_report_exporter_module)

    if hasattr(exporter, "process_and_export_audit_report"):
        export_func = exporter.process_and_export_audit_report
    elif hasattr(exporter, "export_audit_report"):
        export_func = exporter.export_audit_report
    elif hasattr(exporter, "process_audit_report"):
        export_func = exporter.process_audit_report
    elif hasattr(exporter, "export_audit_and_recovery_report"):
        export_func = exporter.export_audit_and_recovery_report
    else:
        export_func = getattr(exporter, "process_audit_report")

    export_report = export_func(
        telemetry_payload=telemetry_payload,
        audit_data=audit_trail,
        epic_id=epic_id,
        incident_id=incident_id,
        module_name=module_name,
        output_path=destination_path
    )

    result_package = {
        "incident_id": incident_id,
        "epic_id": epic_id,
        "audit_trail": audit_trail,
        "export_report": export_report
    }

    os.makedirs(os.path.dirname(os.path.abspath(destination_path)), exist_ok=True)
    with open(destination_path, "w", encoding="utf-8") as f:
        json.dump(result_package, f, default=str)

    return result_package