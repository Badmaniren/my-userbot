from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class AuditExportPipelineError(Exception):
    """Кастомное исключение для ошибок пайплайна аудита и экспорта."""
    pass


class AuditExportPipeline:
    def __init__(self, repo_path=None, log_path=None, threshold=None, audit_hub=None, digest_exporter=None):
        if audit_hub is not None:
            self.hub = audit_hub
        else:
            self.hub = AnomalyAuditHub(
                repo_path=repo_path,
                log_path=log_path,
                threshold=threshold
            )

        if digest_exporter is not None:
            self.exporter = digest_exporter
        else:
            self.exporter = DigestExporter(self.hub)

    def log_and_aggregate_anomaly(self, source, severity, details, telemetry_snapshot, metric_name, value):
        try:
            self.hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
            self.hub.aggregate_and_report(metric_name=metric_name, value=value)
        except Exception as e:
            raise AuditExportPipelineError(str(e))

    def run_audit_and_export_json(self, output_path):
        try:
            self.hub.generate_final_report()
            return self.exporter.export_json_report(output_path)
        except Exception as e:
            raise AuditExportPipelineError(str(e))

    def run_audit_and_export_html(self, output_path):
        try:
            self.hub.generate_final_report()
            return self.exporter.export_html_report(output_path)
        except Exception as e:
            raise AuditExportPipelineError(str(e))

    def export_json(self, output_path):
        return self.run_audit_and_export_json(output_path)

    def export_html(self, output_path):
        return self.run_audit_and_export_html(output_path)