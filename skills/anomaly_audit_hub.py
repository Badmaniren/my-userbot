from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator


class AnomalyAuditHub:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.logger = AnomalyLogger(log_path=log_path)
        self.aggregator = AnomalyReportAggregator(
            repo_path=repo_path,
            log_path=log_path,
            threshold=threshold,
            logger=self.logger
        )

    def log_anomaly(self, source: str, severity: str, details: dict, telemetry_snapshot: dict):
        if details is not None and not isinstance(details, dict):
            raise TypeError("details should be a dictionary")
        if telemetry_snapshot is not None and not isinstance(telemetry_snapshot, dict):
            raise TypeError("telemetry_snapshot should be a dictionary")

        return self.logger.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def aggregate_and_report(self, metric_name: str, value: float):
        if not isinstance(metric_name, str):
            raise TypeError("metric_name must be a string")
        if not isinstance(value, (int, float)):
            raise TypeError("value must be a number")

        return self.aggregator.aggregate_and_report(
            metric_name=metric_name,
            value=value
        )

    def generate_final_report(self):
        return self.aggregator.generate_final_report()