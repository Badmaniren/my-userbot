from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator, AnomalyReportAggregatorError


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
        # Обеспечиваем совместимость атрибутов, ожидавмых юнит-тестами
        self.aggregator.repo_path = repo_path
        self.aggregator.threshold = threshold
        self.logger.log_path = log_path

    def log_anomaly(self, source: str, severity: str, details: dict, telemetry_snapshot: dict):
        result = self.logger.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        if result is None:
            return True
        return result

    def aggregate_and_report(self, metric_name: str, value: float):
        return self.aggregator.aggregate_and_report(
            metric_name=metric_name,
            value=value
        )

    def generate_final_report(self):
        return self.aggregator.generate_final_report()