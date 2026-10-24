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
        return self.logger.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def aggregate_and_report(self, metric_name: str, value: float):
        self.logger.log_anomaly(
            source=metric_name,
            severity="INFO",
            details={"metric_name": metric_name, "value": value},
            telemetry_snapshot={}
        )
        return self.aggregator.aggregate_and_report(
            metric_name=metric_name,
            value=value
        )

    def generate_final_report(self):
        return self.aggregator.generate_final_report()