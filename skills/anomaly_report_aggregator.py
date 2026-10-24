from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_logger import AnomalyLogger


class AnomalyReportAggregatorError(Exception):
    """Исключение для ошибок модуля AnomalyReportAggregator."""
    pass


class AnomalyReportAggregator:
    def __init__(self, repo_path=None, log_path=None, threshold=None, detector=None, correlator=None, logger=None):
        if logger is not None:
            self.anomaly_logger = logger
        elif log_path is not None:
            self.anomaly_logger = AnomalyLogger(log_path=log_path)
        else:
            self.anomaly_logger = AnomalyLogger()

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

    def _extract_anomaly_list(self, anomalies_data):
        if isinstance(anomalies_data, list):
            return anomalies_data
        if isinstance(anomalies_data, dict):
            for key in ("report", "anomalies", "events", "correlated_events", "anomalies_detected"):
                val = anomalies_data.get(key)
                if isinstance(val, list):
                    return val
            if any(k in anomalies_data for k in ("source", "severity", "details", "telemetry_snapshot")):
                return [anomalies_data]
        return []

    def aggregate_and_report(self, metric_name, value):
        try:
            is_anomaly = self.correlator.correlate_metric(metric_name, value)
            if not is_anomaly:
                self.anomaly_logger.log_anomaly(
                    source=metric_name,
                    severity="INFO",
                    details={"metric": metric_name, "value": value}
                )

            anomalies = self.correlator.correlate_events()
            items = self._extract_anomaly_list(anomalies)
            for anomaly in items:
                if isinstance(anomaly, dict):
                    if "id" not in anomaly:
                        self.anomaly_logger.log_anomaly(
                            source=anomaly.get("source"),
                            severity=anomaly.get("severity"),
                            details=anomaly.get("details"),
                            telemetry_snapshot=anomaly.get("telemetry_snapshot")
                        )
                elif isinstance(anomaly, str):
                    self.anomaly_logger.log_anomaly(
                        source=anomaly,
                        severity="INFO",
                        details={"metric": anomaly, "value": value}
                    )

            return self.anomaly_logger.get_structured_report()
        except AnomalyCorrelatorError as e:
            raise AnomalyReportAggregatorError(str(e))
        except Exception as e:
            if isinstance(e, AnomalyReportAggregatorError):
                raise
            raise AnomalyReportAggregatorError(str(e)) from e

    def aggregate_execution_flow(self, execution_id, payload):
        try:
            anomalies = self.correlator.analyze_execution_flow(execution_id, payload)
            
            items = self._extract_anomaly_list(anomalies)
            for anomaly in items:
                if isinstance(anomaly, dict):
                    if "id" not in anomaly:
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
                        details={"execution_id": execution_id, "anomaly": anomaly}
                    )

            return self.anomaly_logger.get_structured_report()
        except Exception as e:
            if isinstance(e, AnomalyReportAggregatorError):
                raise
            raise AnomalyReportAggregatorError(str(e)) from e

    def generate_final_report(self):
        try:
            return self.anomaly_logger.get_structured_report()
        except Exception as e:
            if isinstance(e, AnomalyReportAggregatorError):
                raise
            raise AnomalyReportAggregatorError(str(e)) from e
