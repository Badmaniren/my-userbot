from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class AuditExporterPipeline:
    def __init__(self, repo_path=None, log_path=None, threshold=None, audit_hub=None, exporter=None):
        if audit_hub is not None:
            self.audit_hub = audit_hub
        else:
            self.audit_hub = AnomalyAuditHub(
                repo_path=repo_path,
                log_path=log_path,
                threshold=threshold
            )

        if exporter is not None:
            self.exporter = exporter
            if getattr(self.exporter, "digest", None) is None:
                self.exporter.digest = self.audit_hub
        else:
            self.exporter = DigestExporter(
                stability_digest=self.audit_hub,
                anomaly_visualizer=None
            )

    def run_audit_and_export(self, output_path: str, export_format: str = "json"):
        self.audit_hub.aggregate_and_report()
        self.audit_hub.generate_final_report()

        if export_format.lower() == "html":
            if hasattr(self.exporter, "export_html_report"):
                return self.exporter.export_html_report(output_path)
            return self.exporter.export_report(output_path)
        else:
            if hasattr(self.exporter, "export_json_report"):
                return self.exporter.export_json_report(output_path)
            return self.exporter.export_report(output_path)

    def log_external_anomaly(self, source: str, severity: str, details: dict, telemetry_snapshot: dict):
        self.audit_hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def run_pipeline(self, output_path: str):
        self.audit_hub.aggregate_and_report()
        report_data = self.audit_hub.generate_final_report()
        if hasattr(self.exporter, "export_json_report"):
            return self.exporter.export_json_report(output_path)
        elif hasattr(self.exporter, "export_report"):
            return self.exporter.export_report(output_path)
        else:
            return report_data