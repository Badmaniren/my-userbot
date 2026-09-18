import io
from skills import incident_audit_trail_collector
from skills.recovery_report_exporter import RecoveryReportExporter


class IncidentForensicsAuditArchiver:
    def __init__(self, exporter=None, recovery_exporter=None):
        self._exporter = exporter if exporter is not None else recovery_exporter

    @property
    def exporter(self):
        if self._exporter is not None:
            return self._exporter
        return RecoveryReportExporter()

    @exporter.setter
    def exporter(self, value):
        self._exporter = value

    def archive_incident(
        self,
        incident_data,
        destination_path,
        include_raw_telemetry,
        module_name,
        exception,
        traceback_str
    ):
        audit_result = incident_audit_trail_collector.collect_incident_audit_trail(
            incident_data,
            destination_path,
            include_raw_telemetry
        )

        incident_id = incident_data.get("id") or incident_data.get("incident_id")

        report_result = self.exporter.generate_comprehensive_report(
            module_name,
            exception,
            traceback_str,
            incident_id,
            incident_data
        )

        if isinstance(report_result, dict):
            report_result["incident_id"] = incident_id

        return {
            "incident_id": incident_id,
            "audit_result": audit_result,
            "report_result": report_result
        }

    def finalize_archive_summary(
        self,
        epic_id,
        stream,
        summary_payload,
        export_format
    ):
        if isinstance(stream, str):
            stream = io.BytesIO(stream.encode("utf-8"))
        return self.exporter.finalize_and_export_summary(
            epic_id,
            stream,
            summary_payload,
            export_format
        )

    def finalize_summary_stream(
        self,
        epic_id,
        stream,
        summary_payload,
        export_format
    ):
        return self.finalize_archive_summary(
            epic_id,
            stream,
            summary_payload,
            export_format
        )

    def export_archive_file(
        self,
        report_payload,
        output_path
    ):
        return self.exporter.export_epic_report_file(
            report_payload,
            output_path
        )

    def export_report_file(
        self,
        report_payload,
        output_path
    ):
        return self.export_archive_file(
            report_payload,
            output_path
        )

    def collect_and_export_trail(
        self,
        incident_data,
        destination_path,
        include_raw_telemetry=True
    ):
        return incident_audit_trail_collector.collect_incident_audit_trail(
            incident_data,
            destination_path,
            include_raw_telemetry
        )

    def export_report(
        self,
        module_name,
        exception,
        traceback_str,
        incident_id,
        audit_data,
        epic_id=None,
        stream=None,
        summary_payload=None,
        export_format="json",
        output_path=None
    ):
        report = self.exporter.generate_comprehensive_report(
            module_name,
            exception,
            traceback_str,
            incident_id,
            audit_data
        )

        if summary_payload and stream and epic_id:
            if isinstance(stream, str):
                stream = io.BytesIO(stream.encode("utf-8"))
            self.exporter.finalize_and_export_summary(
                epic_id,
                stream,
                summary_payload,
                export_format
            )

        if output_path:
            if isinstance(report, dict):
                payload_to_export = dict(report)
            else:
                payload_to_export = {"report": report}
            if epic_id:
                payload_to_export["epic_id"] = epic_id
            self.exporter.export_epic_report_file(payload_to_export, output_path)

        return report

    def collect_and_report_incident(
        self,
        incident_data,
        destination_path,
        include_raw_telemetry,
        module_name,
        exception,
        traceback_str
    ):
        return self.archive_incident(
            incident_data,
            destination_path,
            include_raw_telemetry,
            module_name,
            exception,
            traceback_str
        )


incident_forensics_audit_archiver = IncidentForensicsAuditArchiver()


def collect_and_report_incident(
    incident_data,
    destination_path,
    include_raw_telemetry,
    module_name,
    exception,
    traceback_str
):
    return incident_forensics_audit_archiver.archive_incident(
        incident_data,
        destination_path,
        include_raw_telemetry,
        module_name,
        exception,
        traceback_str
    )


def finalize_summary_stream(
    epic_id,
    stream,
    summary_payload,
    export_format
):
    return incident_forensics_audit_archiver.finalize_archive_summary(
        epic_id,
        stream,
        summary_payload,
        export_format
    )


def export_report_file(
    report_payload,
    output_path
):
    return incident_forensics_audit_archiver.export_archive_file(
        report_payload,
        output_path
    )


def archive_incident_forensics_data(
    incident_data,
    destination_path,
    include_raw_telemetry,
    module_name,
    exception,
    traceback_str,
    incident_id,
    epic_id,
    stream,
    summary_payload,
    export_format,
    output_path
):
    archiver = IncidentForensicsAuditArchiver()

    archiver.collect_and_export_trail(
        incident_data=incident_data,
        destination_path=destination_path,
        include_raw_telemetry=include_raw_telemetry
    )

    report_res = archiver.export_report(
        module_name=module_name,
        exception=exception,
        traceback_str=traceback_str,
        incident_id=incident_id,
        audit_data=incident_data,
        epic_id=epic_id,
        stream=stream,
        summary_payload=summary_payload,
        export_format=export_format,
        output_path=output_path
    )

    return report_res