from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator


class AnomalyAuditHubError(Exception):
    """Исключение для ошибок модуля AnomalyAuditHub."""
    pass


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
        try:
            result = self.logger.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
            if result is None:
                return True
            return result
        except Exception as e:
            if isinstance(e, AnomalyAuditHubError):
                raise
            raise AnomalyAuditHubError(str(e)) from e

    def aggregate_and_report(self, metric_name: str, value: float):
        try:
            result = self.aggregator.aggregate_and_report(
                metric_name=metric_name,
                value=value
            )
            if result is None:
                return True
            return result
        except Exception as e:
            if isinstance(e, AnomalyAuditHubError):
                raise
            raise AnomalyAuditHubError(str(e)) from e

    def generate_final_report(self):
        try:
            result = self.aggregator.generate_final_report()
            if result is None:
                return True
            return result
        except Exception as e:
            if isinstance(e, AnomalyAuditHubError):
                raise
            raise AnomalyAuditHubError(str(e)) from e
