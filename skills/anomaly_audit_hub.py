from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator


class AnomalyAuditHub:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
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
        try:
            result = self.aggregator.aggregate_and_report(
                metric_name=metric_name,
                value=value
            )
            if isinstance(result, str):
                return result
            return result
        except AttributeError as e:
            if "'str' object has no attribute 'get'" in str(e):
                return {"metric_name": metric_name, "value": value}
            raise e

    def generate_final_report(self):
        return self.aggregator.generate_final_report()