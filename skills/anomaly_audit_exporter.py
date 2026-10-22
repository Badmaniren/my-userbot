from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_exporter import DigestExporter


class AnomalyAuditExporterError(Exception):
    """Исключение для ошибок модуля AnomalyAuditExporter."""
    pass


class AnomalyAuditExporter:
    """
    Композитный модуль для бесшовного объединения аудиторских отчетов из hub
    и последующего экспорта через digest_exporter.
    """

    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        self.visualizer = AnomalyVisualizer()
        self.digest_exporter = DigestExporter(
            stability_digest=self.hub,
            anomaly_visualizer=self.visualizer
        )

    def aggregate_and_export_json(self, metric_name: str, value, json_path: str):
        try:
            self.hub.aggregate_and_report(metric_name, value)
            report = self.hub.generate_final_report()
            metrics = self.visualizer.digest.get("metrics", {})
            metrics[metric_name] = value
            self.visualizer.digest["metrics"] = metrics
            self.visualizer.digest["anomalies"] = report
            return self.digest_exporter.export_json_report(json_path)
        except Exception as e:
            raise AnomalyAuditExporterError(str(e))

    def export_html(self, html_path: str):
        try:
            report = self.hub.generate_final_report()
            self.visualizer.digest["anomalies"] = report
            return self.digest_exporter.export_html_report(html_path)
        except Exception as e:
            raise AnomalyAuditExporterError(str(e))

    def export_audit_report(self, output_path: str):
        try:
            report = self.hub.generate_final_report()
            self.visualizer.digest["anomalies"] = report
            return self.digest_exporter.export_json_report(output_path)
        except Exception as e:
            raise AnomalyAuditExporterError(str(e))

    def log_external_anomaly(self, source: str, severity: str, details, telemetry_snapshot: dict):
        try:
            self.hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
        except Exception as e:
            raise AnomalyAuditExporterError(str(e))
