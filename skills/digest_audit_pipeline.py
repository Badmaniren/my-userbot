from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter, DigestExporterError


class DigestAuditPipelineError(Exception):
    """Пользовательское исключение для ошибок конвейера дайджеста и аудита."""
    pass


class DigestAuditPipeline:
    """Композитный конвейер, объединяющий аналитику аудита аномалий и экспорт дайджестов."""

    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.audit_hub = AnomalyAuditHub(
            repo_path=repo_path,
            log_path=log_path,
            threshold=threshold
        )
        self.exporter = DigestExporter(self.audit_hub)

    def run_audit_and_export(
        self,
        source: str,
        severity: str,
        details: str,
        telemetry_snapshot: dict,
        metric_name: str,
        metric_value: float,
        output_path: str,
        format_type: str
    ) -> str:
        """Выполняет аудит аномалий и экспортирует отчет в заданном формате."""
        self.audit_hub.log_anomaly(source, severity, details, telemetry_snapshot)
        self.audit_hub.aggregate_and_report(metric_name, metric_value)
        self.audit_hub.generate_final_report()

        fmt = format_type.lower()
        try:
            if fmt == "json":
                return self.exporter.export_to_json(output_path)
            elif fmt == "html":
                return self.exporter.export_to_html(output_path)
            else:
                raise DigestAuditPipelineError(f"Unsupported format type: {format_type}")
        except Exception as e:
            if isinstance(e, DigestAuditPipelineError):
                raise
            raise DigestAuditPipelineError(f"Export failed: {e}")

    def export_comprehensive_json(self, output_path: str) -> str:
        """Экспортирует комплексный отчет в формате JSON."""
        try:
            return self.exporter.export_to_json(output_path)
        except Exception as e:
            raise DigestAuditPipelineError(f"Comprehensive JSON export failed: {e}")

    def export_comprehensive_html(self, output_path: str) -> str:
        """Экспортирует комплексный отчет в формате HTML."""
        try:
            return self.exporter.export_to_html(output_path)
        except Exception as e:
            raise DigestAuditPipelineError(f"Comprehensive HTML export failed: {e}")