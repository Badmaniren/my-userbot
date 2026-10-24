from typing import Dict, Any
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator


class AnomalyAuditHubError(Exception):
    """Кастомное исключение для модуля AnomalyAuditHub."""
    pass


class AnomalyAuditHub:
    """
    Центральный узел для аудита аномалий, делегирующий задачи
    логирования и агрегации отчетов.
    """

    def __init__(self, repo_path: str, log_path: str, threshold: float) -> None:
        """
        Инициализация компонентов аудита.
        """
        if not repo_path or not log_path:
            raise AnomalyAuditHubError("repo_path and log_path must not be empty.")
        self.repo_path: str = repo_path
        self.log_path: str = log_path
        self.threshold: float = threshold
        try:
            self.logger: AnomalyLogger = AnomalyLogger(log_path=log_path)
            self.aggregator: AnomalyReportAggregator = AnomalyReportAggregator(
                repo_path=repo_path,
                log_path=log_path,
                threshold=threshold,
                logger=self.logger
            )
        except Exception as e:
            raise AnomalyAuditHubError(f"Initialization failed: {e}") from e

    def log_anomaly(
        self,
        source: str,
        severity: str,
        details: Dict[str, Any],
        telemetry_snapshot: Dict[str, Any]
    ) -> Any:
        """
        Делегирует запись аномалии в лог-файл.
        """
        try:
            return self.logger.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
        except Exception as e:
            if isinstance(e, AnomalyAuditHubError):
                raise
            raise AnomalyAuditHubError(f"Failed to log anomaly: {e}") from e

    def aggregate_and_report(self, metric_name: str, value: float) -> Any:
        """
        Делегирует агрегацию метрики и проверку порога аномалий.
        """
        try:
            return self.aggregator.aggregate_and_report(
                metric_name=metric_name,
                value=value
            )
        except Exception as e:
            if isinstance(e, AnomalyAuditHubError):
                raise
            raise AnomalyAuditHubError(f"Failed to aggregate and report: {e}") from e

    def generate_final_report(self) -> Dict[str, Any]:
        """
        Делегирует генерацию итогового отчета по накопленным данным.
        """
        try:
            return self.aggregator.generate_final_report()
        except Exception as e:
            if isinstance(e, AnomalyAuditHubError):
                raise
            raise AnomalyAuditHubError(f"Failed to generate final report: {e}") from e
