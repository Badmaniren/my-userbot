from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class AuditExportPipelineError(Exception):
    """Исключение, используемое в конвейере аудита и экспорта."""
    pass


class AuditExportPipeline:
    """Конвейер для агрегации аномалий и автоматического экспорта отчетов аудита безопасности."""

    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

        # Композиция: инициализация существующих навыков
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.exporter = DigestExporter(self.hub)

    def run_pipeline_and_export(self, metric_name: str, value: float, output_path: str, export_format: str):
        try:
            self.hub.aggregate_and_report(metric_name, value)
            self.hub.generate_final_report()

            fmt = export_format.lower()
            if fmt == "json":
                return self.exporter.export_to_json(output_path)
            elif fmt == "html":
                return self.exporter.export_to_html(output_path)
            else:
                raise AuditExportPipelineError(f"Unsupported export format: {export_format}")
        except Exception as e:
            if isinstance(e, AuditExportPipelineError):
                raise
            raise AuditExportPipelineError(str(e)) from e

    def record_anomaly_and_export_report(self, source: str, severity: str, details, telemetry_snapshot, output_path: str):
        try:
            self.hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
            return self.exporter.export_json_report(output_path)
        except Exception as e:
            raise AuditExportPipelineError(str(e)) from e

    def run_export(self, output_path: str) -> str:
        try:
            report_data = self.hub.generate_final_report()
            import json
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=4)
            return output_path
        except Exception as e:
            raise AuditExportPipelineError(str(e)) from e