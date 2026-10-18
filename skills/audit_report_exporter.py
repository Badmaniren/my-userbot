from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class AuditReportExporterError(Exception):
    """Исключение, возникающее при ошибках экспорта отчетов аудита."""
    pass


class AuditReportExporter:
    """
    Модуль экспорта аудиторских отчетов, объединяющий функционал
    anomaly_audit_hub и digest_exporter для генерации и выгрузки надежных отчетов безопасности.
    """

    def __init__(self, repo_path=None, log_path=None, threshold=None, anomaly_audit_hub=None, digest_exporter=None):
        if anomaly_audit_hub is not None:
            self.anomaly_audit_hub = anomaly_audit_hub
        else:
            self.anomaly_audit_hub = AnomalyAuditHub(
                repo_path=repo_path,
                log_path=log_path,
                threshold=threshold
            )

        if digest_exporter is not None:
            self.digest_exporter = digest_exporter
        else:
            self.digest_exporter = DigestExporter()

    def export_json_report(self, output_path: str) -> str:
        try:
            return self.digest_exporter.export_json_report(output_path)
        except Exception as e:
            raise AuditReportExporterError(f"Export failed: {e}") from e

    def export_html_report(self, output_path: str) -> str:
        try:
            return self.digest_exporter.export_html_report(output_path)
        except Exception as e:
            raise AuditReportExporterError(f"HTML Export error: {e}") from e

    def aggregate_and_report(self, metric: str, value):
        res = self.anomaly_audit_hub.aggregate_and_report(metric, value)
        if res is not None:
            return res
        return {"metric": metric, "value": value}

    def log_anomaly(self, source: str, severity: str, details, telemetry):
        res = self.anomaly_audit_hub.log_anomaly(source, severity, details, telemetry)
        if res is not None:
            return res
        return {"source": source, "severity": severity, "details": details, "telemetry": telemetry}

    def export_stream_to_json(self, stream_id: str, output_path) -> str:
        return self.digest_exporter.export_stream_to_json(stream_id, output_path)

    def export_to_json(self, output_path: str) -> str:
        try:
            if hasattr(self.digest_exporter, 'export_to_json'):
                return self.digest_exporter.export_to_json(output_path)
            return self.digest_exporter.export_json_report(output_path)
        except Exception as e:
            raise AuditReportExporterError(f"Export to JSON failed: {e}") from e