from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter, DigestExporterError


class AuditExportPipeline:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.digest_exporter = DigestExporter(self.audit_hub)

    def run_audit_and_export_json(self, output_path: str) -> str:
        self.audit_hub.generate_final_report()
        return self.digest_exporter.export_json_report(output_path)

    def run_audit_and_export_html(self, output_path: str) -> str:
        self.audit_hub.generate_final_report()
        return self.digest_exporter.export_html_report(output_path)

    def aggregate_metric(self, metric_name: str, value: float) -> None:
        self.audit_hub.aggregate_and_report(metric_name, value)

    def log_pipeline_anomaly(self, source: str, severity: str, details: any, telemetry: dict) -> None:
        self.audit_hub.log_anomaly(source, severity, details, telemetry)

    def export_report(self, output_path: str, format: str = "json") -> str:
        self.audit_hub.generate_final_report()
        if format.lower() == "html":
            return self.digest_exporter.export_html_report(output_path)
        return self.digest_exporter.export_json_report(output_path)