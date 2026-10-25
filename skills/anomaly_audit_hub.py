from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator, AnomalyReportAggregatorError


class AnomalyAuditHubError(Exception):
    """Исключение для ошибок модуля AnomalyAuditHub."""
    pass


class AnomalyAuditHub:
    """Центральный модуль аудита аномалий."""

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

    def log_anomaly(self, source, severity=None, details=None, telemetry_snapshot=None):
        try:
            result = self.logger.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
            if result is None:
                return {}
            return result
        except Exception:
            raise

    def aggregate_and_report(self, metric_name: str, value: float):
        try:
            return self.aggregator.aggregate_and_report(
                metric_name=metric_name,
                value=value
            )
        except Exception:
            raise

    def generate_final_report(self):
        try:
            return self.aggregator.generate_final_report()
        except Exception:
            raise