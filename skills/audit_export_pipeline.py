from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_exporter import DigestExporter, DigestExporterError


class AuditExportPipelineError(Exception):
    """Custom exception for AuditExportPipeline errors."""
    pass


class AuditExportPipeline:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.audit_hub = AnomalyAuditHub(
            repo_path=repo_path,
            log_path=log_path,
            threshold=threshold
        )
        self.visualizer = AnomalyVisualizer()
        self.exporter = DigestExporter(
            stability_digest=self.audit_hub,
            anomaly_visualizer=self.visualizer
        )

    def log_and_export(
        self,
        source: str,
        severity: str,
        details: str,
        telemetry_snapshot: dict,
        output_path: str
    ) -> str:
        try:
            self.audit_hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
            return self.exporter.export_json_report(output_path)
        except Exception as e:
            raise AuditExportPipelineError(f"Pipeline failed during log_and_export: {e}")

    def export_html(self, output_path: str) -> str:
        self.audit_hub.generate_final_report()
        return self.exporter.export_html_report(output_path)

    def aggregate_metric(self, metric_name: str, value: float):
        return self.audit_hub.aggregate_and_report(metric_name, value)

    def export_report(self, output_path: str, format: str = "json") -> str:
        if format.lower() == "html":
            return self.exporter.export_html_report(output_path)
        else:
            return self.exporter.export_json_report(output_path)