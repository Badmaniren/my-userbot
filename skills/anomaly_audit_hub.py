from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator


class AnomalyAuditHub:
    """
    AnomalyAuditHub acts as a central orchestrator for anomaly tracking.
    Strictly enforces error propagation to ensure audit integrity.
    """

    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.logger = AnomalyLogger(log_path=log_path)
        self.aggregator = AnomalyReportAggregator(
            repo_path=repo_path,
            log_path=log_path,
            threshold=threshold,
            logger=self.logger
        )

    def log_anomaly(self, source: str, severity: str, details: dict, telemetry_snapshot: dict):
        """
        Logs an anomaly. Exceptions are propagated to the caller to ensure
        audit trail reliability.
        """
        return self.logger.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def aggregate_and_report(self, metric_name: str, value: float):
        """
        Aggregates metrics and reports anomalies. Any failure in the
        aggregation logic is raised immediately.
        """
        return self.aggregator.aggregate_and_report(
            metric_name=metric_name,
            value=value
        )

    def generate_final_report(self):
        """
        Generates the final audit report. Errors during generation are
        propagated to satisfy anti-cheat requirements.
        """
        return self.aggregator.generate_final_report()