from typing import Any, Dict, List, Optional, Union
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator, AnomalyReportAggregatorError


class AnomalyAuditHub:
    """Узел аудита аномалий, объединяющий логгер и агрегатор отчетов."""

    def __init__(self, repo_path: str, log_path: str, threshold: float) -> None:
        self.repo_path: str = repo_path
        self.log_path: str = log_path
        self.threshold: float = threshold
        self.logger: AnomalyLogger = AnomalyLogger(log_path=self.log_path)
        self.aggregator: AnomalyReportAggregator = AnomalyReportAggregator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
            logger=self.logger
        )

    def log_anomaly(
        self,
        source: Optional[str] = None,
        severity: Optional[str] = None,
        details: Any = None,
        telemetry_snapshot: Optional[Dict[str, Any]] = None
    ) -> Any:
        return self.logger.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def aggregate_and_report(self, metric_name: str, value: float) -> Union[Dict[str, Any], List[Any]]:
        return self.aggregator.aggregate_and_report(metric_name=metric_name, value=value)

    def generate_final_report(self) -> Union[Dict[str, Any], List[Any]]:
        return self.aggregator.generate_final_report()
