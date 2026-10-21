from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class AuditExportPipelineError(Exception):
    """Кастомное исключение для ошибок конвейера аудита и экспорта."""
    pass


class AuditExportPipeline:
    """
    Композитный модуль для связывания агрегатора аудита (AnomalyAuditHub)
    и экспортера дайджестов (DigestExporter) в единый конвейер выгрузки отчетов безопасности.
    """

    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

        # Инициализация зависимостей в рамках композиции
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.digest_exporter = DigestExporter(self.audit_hub)

    def aggregate_metric(self, metric_name: str, value: float):
        """Агрегирует метрику через внутренний audit_hub с позиционными аргументами."""
        return self.audit_hub.aggregate_and_report(metric_name, value)

    def log_pipeline_anomaly(self, source: str, severity: str, details, telemetry: dict):
        """Логирует аномалию безопасности через audit_hub."""
        self.audit_hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry
        )

    def export_report(self, output_path: str, format_type: str = 'json') -> str:
        """
        Генерирует финальный отчет через audit_hub и экспортирует его
        в заданном формате с помощью digest_exporter.
        """
        try:
            # Генерация финального отчета в аудит хабе
            self.audit_hub.generate_final_report()

            fmt = format_type.lower()
            if fmt == 'json':
                return self.digest_exporter.export_to_json(output_path)
            elif fmt == 'html':
                return self.digest_exporter.export_to_html(output_path)
            else:
                raise AuditExportPipelineError(f"Unsupported format type: {format_type}")
        except Exception as e:
            if isinstance(e, AuditExportPipelineError):
                raise e
            raise AuditExportPipelineError(f"Failed to export report: {e}")

    def export_pipeline_report(self, output_path: str) -> str:
        """
        Метод интеграционного теста для экспорта отчета (по умолчанию в формате json).
        """
        try:
            self.audit_hub.generate_final_report()
            if hasattr(self.digest_exporter, 'export_to_json'):
                return self.digest_exporter.export_to_json(output_path)
            elif hasattr(self.digest_exporter, 'export'):
                return self.digest_exporter.export(output_path)
            else:
                return self.digest_exporter.export_to_json(output_path)
        except Exception as e:
            raise AuditExportPipelineError(f"Integration export failed: {e}")