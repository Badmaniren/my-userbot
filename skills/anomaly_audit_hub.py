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
        # Обеспечиваем наличие атрибутов для юнит-тестов, ожидающих их на агрегаторе
        self.aggregator.repo_path = repo_path
        self.aggregator.log_path = log_path
        self.aggregator.threshold = threshold

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
            if result is None:
                return {}
            return result
        except AnomalyReportAggregatorError:
            raise
        except Exception as e:
            self.logger.log_anomaly(
                source="AnomalyAuditHub",
                severity="ERROR",
                details={"error": str(e), "metric": metric_name},
                telemetry_snapshot={}
            )
            return {}

    def generate_final_report(self):
        report = self.aggregator.generate_final_report()
        if report is None:
            report = {"anomalies": []}
        elif isinstance(report, list):
            report = {"anomalies": report}
        elif isinstance(report, dict):
            if "anomalies" not in report:
                report["anomalies"] = []
        else:
            report = {"anomalies": []}

        return report