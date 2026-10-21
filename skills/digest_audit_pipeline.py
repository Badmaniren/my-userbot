from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class DigestAuditPipelineError(Exception):
    """Кастомное исключение для ошибок конвейера дайджеста и аудита."""
    pass


class DigestAuditPipeline:
    def __init__(self, repo_path=None, log_path=None, threshold=None, audit_hub=None, exporter=None):
        repo_path = repo_path if repo_path is not None else "."
        log_path = log_path if log_path is not None else "/tmp/anomaly_audit.log"
        threshold = threshold if threshold is not None else 0.5

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
        else:
            self.exporter = DigestExporter()

    def log_anomaly(self, source, severity, details, telemetry_snapshot=None):
        return self.audit_hub.log_anomaly(source, severity, details, telemetry_snapshot)

    def aggregate_and_report(self, metric_name, value):
        return self.audit_hub.aggregate_and_report(metric_name, value)

    def run_audit_and_export_json(self, output_path):
        try:
            self.audit_hub.generate_final_report()
            return self.exporter.export_json_report(output_path)
        except Exception as e:
            raise DigestAuditPipelineError(str(e))

    def run_audit_and_export_html(self, output_path):
        try:
            self.audit_hub.generate_final_report()
            return self.exporter.export_html_report(output_path)
        except Exception as e:
            raise DigestAuditPipelineError(str(e))

    def run_audit_and_export(self, output_path):
        try:
            self.audit_hub.generate_final_report()
            if output_path.endswith(".html"):
                return self.exporter.export_html_report(output_path)
            else:
                return self.exporter.export_json_report(output_path)
        except Exception as e:
            raise DigestAuditPipelineError(str(e))