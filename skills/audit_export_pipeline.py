from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_exporter import DigestExporter


class AuditExportPipelineError(Exception):
    """Кастомное исключение для конвейера выгрузки аудита."""
    pass


class AuditExportPipeline:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.audit_hub = self.hub
        self.visualizer = AnomalyVisualizer()

        self.exporter = DigestExporter(stability_digest=self.hub, anomaly_visualizer=self.visualizer)

    def record_anomaly(self, source: str, severity: str, details: str, telemetry_snapshot: dict):
        return self.hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def aggregate_metric(self, metric_name, value=None):
        if isinstance(metric_name, dict):
            return self.hub.aggregate_and_report(metric_name)
        elif value is not None or isinstance(metric_name, str):
            return self.hub.aggregate_and_report(metric_name=metric_name, value=value)
        else:
            anomaly_data = {
                "source": str(metric_name),
                "severity": "INFO",
                "details": str(value),
                "telemetry_snapshot": {}
            }
            return self.hub.aggregate_and_report(anomaly_data)

    def run_export(self, output_path: str, format_type: str) -> str:
        report_data = self.hub.generate_final_report()
        if isinstance(report_data, dict):
            self.visualizer.digest = report_data
        elif isinstance(report_data, list):
            self.visualizer.digest = {"report": report_data}
        else:
            self.visualizer.digest = {"data": report_data}

        fmt = format_type.lower()
        if fmt == 'json':
            return self.exporter.export_to_json(output_path)
        elif fmt == 'html':
            return self.exporter.export_to_html(output_path)
        else:
            raise AuditExportPipelineError(f"Unsupported format type: {format_type}")

    def export_pipeline_report(self, output_path: str, format_type: str) -> str:
        return self.run_export(output_path=output_path, format_type=format_type)
