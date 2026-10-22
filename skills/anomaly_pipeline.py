from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class AnomalyPipeline:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.logger = AnomalyLogger(
            log_path=self.log_path
        )

    def process_anomaly(self, source: str, severity, details, telemetry_snapshot: dict):
        self.audit_hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        self.logger.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def process_and_log_anomaly(self, source: str, severity, details, telemetry_snapshot: dict):
        self.process_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def aggregate_pipeline_metric(self, metric_name: str, metric_value: float):
        return self.audit_hub.aggregate_and_report(metric_name, metric_value)

    def generate_final_report(self):
        return self.audit_hub.generate_final_report()

    def get_pipeline_structured_report(self) -> str:
        return self.logger.get_structured_report()