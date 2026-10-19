from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class AnomalyAuditBridgeError(Exception):
    """Пользовательское исключение для ошибок модуля AnomalyAuditBridge."""
    pass


class AnomalyAuditBridge:
    """Связующий модуль для интеграции хаба аудита и экспортера дайджестов."""

    def __init__(self, repo_path_or_hub=None, log_path=None, threshold=None, digest_exporter=None, audit_hub=None):
        try:
            if audit_hub is not None:
                self.audit_hub = audit_hub
                self.digest_exporter = digest_exporter if digest_exporter is not None else DigestExporter()
            elif isinstance(AnomalyAuditHub, type) and isinstance(repo_path_or_hub, AnomalyAuditHub):
                self.audit_hub = repo_path_or_hub
                self.digest_exporter = digest_exporter if digest_exporter is not None else DigestExporter()
            elif hasattr(repo_path_or_hub, "log_anomaly") or hasattr(repo_path_or_hub, "aggregate_and_report"):
                self.audit_hub = repo_path_or_hub
                self.digest_exporter = digest_exporter if digest_exporter is not None else DigestExporter()
            else:
                self.audit_hub = AnomalyAuditHub(repo_path_or_hub, log_path, threshold)
                self.digest_exporter = digest_exporter if digest_exporter is not None else DigestExporter()
        except Exception as e:
            if isinstance(e, AnomalyAuditBridgeError):
                raise
            raise AnomalyAuditBridgeError(str(e)) from e

    def log_anomaly(self, source, severity, details, telemetry):
        try:
            res = self.audit_hub.log_anomaly(source, severity, details, telemetry)
            if res is None:
                return True
            return res
        except Exception as e:
            if isinstance(e, AnomalyAuditBridgeError):
                raise
            raise AnomalyAuditBridgeError(str(e)) from e

    def aggregate_and_report(self, metric_name, value):
        try:
            return self.audit_hub.aggregate_and_report(metric_name, value)
        except Exception as e:
            if isinstance(e, AnomalyAuditBridgeError):
                raise
            raise AnomalyAuditBridgeError(str(e)) from e

    def generate_final_report(self):
        try:
            return self.audit_hub.generate_final_report()
        except Exception as e:
            if isinstance(e, AnomalyAuditBridgeError):
                raise
            raise AnomalyAuditBridgeError(str(e)) from e

    def export_json_report(self, output_path):
        try:
            return self.digest_exporter.export_json_report(output_path)
        except Exception as e:
            if isinstance(e, AnomalyAuditBridgeError):
                raise
            raise AnomalyAuditBridgeError(str(e)) from e

    def export_html_report(self, output_path):
        try:
            return self.digest_exporter.export_html_report(output_path)
        except Exception as e:
            if isinstance(e, AnomalyAuditBridgeError):
                raise
            raise AnomalyAuditBridgeError(str(e)) from e

    def export_stream_to_json(self, stream_id, output_path):
        try:
            return self.digest_exporter.export_stream_to_json(stream_id, output_path)
        except Exception as e:
            if isinstance(e, AnomalyAuditBridgeError):
                raise
            raise AnomalyAuditBridgeError(str(e)) from e

    def process_and_export(self, output_path):
        try:
            report = self.audit_hub.generate_final_report()
            if hasattr(self.digest_exporter, "stability_digest") and hasattr(self.digest_exporter.stability_digest, "add_digest"):
                self.digest_exporter.stability_digest.add_digest(report)
            if hasattr(self.digest_exporter, "visualizer") and self.digest_exporter.visualizer is not None:
                if hasattr(self.digest_exporter.visualizer, "visualize_digest"):
                    self.digest_exporter.visualizer.visualize_digest(report)
            return self.digest_exporter.export_json_report(output_path)
        except Exception as e:
            if isinstance(e, AnomalyAuditBridgeError):
                raise
            raise AnomalyAuditBridgeError(str(e)) from e