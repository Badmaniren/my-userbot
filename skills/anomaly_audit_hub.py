from typing import Dict, Any
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator


class AnomalyAuditHub:
    """
    Центральный узел для аудита аномалий, делегирующий задачи
    логирования и агрегации отчетов.
    """

    def __init__(self, repo_path: str, log_path: str, threshold: float) -> None:
        """
        Инициализация компонентов аудита.
        """
        self.logger: AnomalyLogger = AnomalyLogger(log_path=log_path)
        self.aggregator: AnomalyReportAggregator = AnomalyReportAggregator(
            repo_path=repo_path,
            log_path=log_path,
            threshold=threshold,
            logger=self.logger
        )

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
        return self.logger.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

    def aggregate_and_report(self, metric_name: str, value: float) -> Any:
        """
        Делегирует агрегацию метрики и проверку порога аномалий.
        """
        return self.aggregator.aggregate_and_report(
            metric_name=metric_name,
            value=value
        )

    def generate_final_report(self) -> Dict[str, Any]:
        """
        Делегирует генерацию итогового отчета по накопленным данным.
        """
        return self.aggregator.generate_final_report()