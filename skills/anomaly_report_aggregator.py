"""
skills/anomaly_report_aggregator.py
Модуль для агрегации данных об аномалиях, группировки инцидентов и формирования сводок.
"""

from typing import Any, Dict, List, Optional
from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_logger import AnomalyLogger


class AnomalyReportAggregatorError(Exception):
    """Кастомное исключение для ошибок модуля AnomalyReportAggregator."""
    pass


class AnomalyReportAggregator:
    """
    Агрегатор отчетов об аномалиях.
    Связывает компоненты обнаружения и логирования аномалий.
    """

    def __init__(
        self,
        repo_path: Optional[str] = None,
        log_path: Optional[str] = None,
        threshold: Optional[float] = None,
        detector: Optional[Any] = None,
        correlator: Optional[Any] = None,
        logger: Optional[Any] = None
    ) -> None:
        if logger is not None:
            self.anomaly_logger = logger
            self.logger = logger
        else:
            actual_log_path = log_path or "/tmp/anomaly_report.log"
            self.anomaly_logger = AnomalyLogger(log_path=actual_log_path)
            self.logger = self.anomaly_logger

        if correlator is not None:
            self.correlator = correlator
        else:
            self.correlator = AnomalyCorrelator(
                repo_path=repo_path,
                log_path=log_path,
                threshold=threshold,
                detector=detector,
                logger=self.anomaly_logger
            )

    def aggregate_and_report(self, metric_name: str, value: Any) -> Any:
        """
        Агрегирует метрику, проводит корреляционный анализ и формирует отчет.
        """
        try:
            self.correlator.correlate_metric(metric_name, value)
            events = self.correlator.correlate_events()

            if isinstance(events, list):
                anomalies = events
            elif isinstance(events, dict):
                anomalies = events.get("report") or events.get("anomalies") or events.get("events") or []
                if not isinstance(anomalies, list):
                    anomalies = [events]
            else:
                anomalies = []

            for anomaly in anomalies:
                if isinstance(anomaly, dict):
                    self.anomaly_logger.log_anomaly(
                        source=anomaly.get("source"),
                        severity=anomaly.get("severity"),
                        details=anomaly.get("details"),
                        telemetry_snapshot=anomaly.get("telemetry_snapshot")
                    )
                elif isinstance(anomaly, str):
                    self.anomaly_logger.log_anomaly(
                        source=anomaly,
                        severity="WARNING",
                        details={"metric": metric_name, "value": value},
                        telemetry_snapshot={}
                    )

            return self.anomaly_logger.get_structured_report()
        except Exception as e:
            raise AnomalyReportAggregatorError(str(e)) from e

    def aggregate_execution_flow(self, execution_id: str, metrics_payload: Any) -> Any:
        """
        Анализирует и агрегирует метрики потока выполнения.
        """
        try:
            anomalies = self.correlator.analyze_execution_flow(execution_id, metrics_payload)

            if isinstance(anomalies, list):
                for anomaly in anomalies:
                    if isinstance(anomaly, dict):
                        self.anomaly_logger.log_anomaly(
                            source=anomaly.get("source"),
                            severity=anomaly.get("severity"),
                            details=anomaly.get("details"),
                            telemetry_snapshot=anomaly.get("telemetry_snapshot")
                        )
                    elif isinstance(anomaly, str):
                        self.anomaly_logger.log_anomaly(
                            source=anomaly,
                            severity="WARNING",
                            details={"execution_id": execution_id},
                            telemetry_snapshot={}
                        )
            elif isinstance(anomalies, dict):
                if "source" in anomalies or "severity" in anomalies or "details" in anomalies:
                    self.anomaly_logger.log_anomaly(
                        source=anomalies.get("source"),
                        severity=anomalies.get("severity"),
                        details=anomalies.get("details"),
                        telemetry_snapshot=anomalies.get("telemetry_snapshot")
                    )
                elif "anomalies_detected" in anomalies:
                    for item in anomalies["anomalies_detected"]:
                        if isinstance(item, dict):
                            self.anomaly_logger.log_anomaly(
                                source=item.get("source"),
                                severity=item.get("severity"),
                                details=item.get("details"),
                                telemetry_snapshot=item.get("telemetry_snapshot")
                            )
                        else:
                            self.anomaly_logger.log_anomaly(
                                source=str(item),
                                severity="WARNING",
                                details={"execution_id": execution_id},
                                telemetry_snapshot={}
                            )

            return self.anomaly_logger.get_structured_report()
        except Exception as e:
            raise AnomalyReportAggregatorError(str(e)) from e

    def generate_final_report(self) -> Any:
        """
        Формирует и возвращает финальный структурированный отчет.
        """
        try:
            return self.anomaly_logger.get_structured_report()
        except Exception as e:
            raise AnomalyReportAggregatorError(str(e)) from e
