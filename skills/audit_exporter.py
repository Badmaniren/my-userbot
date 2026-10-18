import os
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter
from skills.anomaly_visualizer import AnomalyVisualizer


class AuditExporterError(Exception):
    pass


class AuditExporter:
    def __init__(self, repo_path=".", log_path="/tmp/anomaly_audit.log", threshold=0.5, audit_hub=None, digest_exporter=None):
        if repo_path is None:
            repo_path = "."
        if log_path is None:
            log_path = "/tmp/anomaly_audit.log"
        if threshold is None:
            threshold = 0.5

        if audit_hub is not None:
            self.audit_hub = audit_hub
        else:
            dir_name = os.path.dirname(log_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            self.audit_hub = AnomalyAuditHub(
                repo_path=repo_path,
                log_path=log_path,
                threshold=threshold
            )

        if digest_exporter is not None:
            self.digest_exporter = digest_exporter
        else:
            try:
                self.digest_exporter = DigestExporter(
                    stability_digest=self.audit_hub,
                    anomaly_visualizer=AnomalyVisualizer()
                )
            except TypeError:
                self.digest_exporter = DigestExporter()

    def log_anomaly(self, source, severity, details, telemetry_snapshot=None):
        self.audit_hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def generate_final_report(self):
        return self.audit_hub.generate_final_report()

    def export_json_report(self, output_path):
        try:
            return self.digest_exporter.export_json_report(output_path)
        except Exception as e:
            raise AuditExporterError(str(e))

    def export_html_report(self, output_path):
        try:
            return self.digest_exporter.export_html_report(output_path)
        except Exception as e:
            raise AuditExporterError(str(e))

    def export_stream_to_json(self, stream_id, output_path):
        try:
            return self.digest_exporter.export_stream_to_json(stream_id, output_path)
        except Exception as e:
            raise AuditExporterError(str(e))

    def export_audit_report(self, output_path):
        try:
            if hasattr(self.digest_exporter, "export_audit_report"):
                return self.digest_exporter.export_audit_report(output_path)
            return self.export_json_report(output_path)
        except Exception as e:
            raise AuditExporterError(str(e))