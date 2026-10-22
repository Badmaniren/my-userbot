from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator


class AnomalyAuditHubError(Exception):
    """Исключение для ошибок модуля AnomalyAuditHub."""
    pass


class AnomalyAuditHub:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        if not repo_path or not isinstance(repo_path, str):
            raise AnomalyAuditHubError("repo_path must be a non-empty string")
        if not log_path or not isinstance(log_path, str):
            raise AnomalyAuditHubError("log_path must be a non-empty string")
        if not isinstance(threshold, (int, float)):
            raise AnomalyAuditHubError("threshold must be a numeric value")

        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = float(threshold)

        try:
            self.logger = AnomalyLogger(log_path=log_path)
            self.aggregator = AnomalyReportAggregator(
                repo_path=repo_path,
                log_path=log_path,
                threshold=threshold,
                logger=self.logger
            )
        except Exception as e:
            raise AnomalyAuditHubError(f"Failed to initialize AnomalyAuditHub: {e}") from e

    def log_anomaly(self, source: str, severity: str, details: dict, telemetry_snapshot: dict):
        try:
            return self.logger.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
        except Exception as e:
            raise AnomalyAuditHubError(f"Error logging anomaly: {e}") from e

    def aggregate_and_report(self, metric_name: str, value: float):
        try:
            logs = self.logger.get_anomalies()
            fixed = False
            for i, entry in enumerate(logs):
                if isinstance(entry, str):
                    logs[i] = {"source": entry, "details": {}}
                    fixed = True
                elif not isinstance(entry, dict):
                    logs[i] = {"source": str(entry), "details": {}}
                    fixed = True
            if fixed and hasattr(self.logger, "anomalies"):
                self.logger.anomalies = logs

            return self.aggregator.aggregate_and_report(
                metric_name=metric_name,
                value=value
            )
        except Exception as e:
            if isinstance(e, AnomalyAuditHubError):
                raise
            raise AnomalyAuditHubError(f"Error aggregating and reporting anomalies: {e}") from e

    def generate_final_report(self):
        try:
            return self.aggregator.generate_final_report()
        except Exception as e:
            if isinstance(e, AnomalyAuditHubError):
                raise
            raise AnomalyAuditHubError(f"Error generating final report: {e}") from e