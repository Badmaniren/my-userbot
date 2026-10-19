from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class AnomalyAuditExporterError(Exception):
    """Исключение для ошибок модуля AnomalyAuditExporter."""
    pass


class AnomalyAuditExporter:
    """
    Композитный модуль, объединяющий anomaly_audit_hub и digest_exporter
    для автоматического формирования и выгрузки отчетов безопасности.
    """

    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.digest_exporter = DigestExporter()

    def log_and_export_json(self, source: str, severity: str, details: dict, telemetry_snapshot: dict, output_path: str) -> str:
        try:
            self.audit_hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
            return self.digest_exporter.export_json_report(output_path)
        except Exception as e:
            if isinstance(e, AnomalyAuditExporterError):
                raise
            raise AnomalyAuditExporterError(str(e)) from e

    def run_audit_and_export_html(self, metric_name: str, value: float, output_path: str) -> str:
        try:
            # Превращаем details в словарь, если интеграционный тест передает строку,
            # чтобы избежать падения в нижележащих аггрегаторах.
            details = {"metric_name": metric_name, "value": value}
            self.audit_hub.log_anomaly(
                source=metric_name,
                severity="INFO",
                details=details,
                telemetry_snapshot={"value": value}
            )
            self.audit_hub.aggregate_and_report(
                metric_name=metric_name,
                value=value
            )
            self.audit_hub.generate_final_report()
            return self.digest_exporter.export_html_report(output_path)
        except Exception as e:
            if isinstance(e, AnomalyAuditExporterError):
                raise
            raise AnomalyAuditExporterError(str(e)) from e

    def export_stream(self, stream_id: str, output_path: str) -> str:
        try:
            return self.digest_exporter.export_stream_to_json(stream_id, output_path)
        except Exception as e:
            if isinstance(e, AnomalyAuditExporterError):
                raise
            raise AnomalyAuditExporterError(str(e)) from e

    def export_json_report(self, output_path: str) -> str:
        try:
            return self.digest_exporter.export_json_report(output_path)
        except Exception as e:
            if isinstance(e, AnomalyAuditExporterError):
                raise
            raise AnomalyAuditExporterError(str(e)) from e

    def export_html_report(self, output_path: str) -> str:
        try:
            return self.digest_exporter.export_html_report(output_path)
        except Exception as e:
            if isinstance(e, AnomalyAuditExporterError):
                raise
            raise AnomalyAuditExporterError(str(e)) from e