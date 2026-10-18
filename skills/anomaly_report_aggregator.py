from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_logger import AnomalyLogger


class AnomalyReportAggregatorError(Exception):
    """Исключение для ошибок модуля AnomalyReportAggregator."""
    pass


class AnomalyReportAggregator:
    def __init__(self, repo_path=None, log_path=None, threshold=None, detector=None, correlator=None, logger=None):
        if logger is not None:
            self.anomaly_logger = logger
        else:
            self.anomaly_logger = AnomalyLogger(log_path=log_path or "/tmp/anomaly_report.log")

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

    def aggregate_and_report(self, metric_name, value):
        try:
            self.correlator.correlate_metric(metric_name, value)
            events = self.correlator.correlate_events()
            
            if isinstance(events, dict):
                anomalies = events.get("report", [])
            elif isinstance(events, list):
                anomalies = events
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
                        details={"metric": metric_name, "value": value}
                    )
                
            return self.anomaly_logger.get_structured_report()
        except AnomalyCorrelatorError as e:
            raise AnomalyReportAggregatorError(str(e))

    def aggregate_execution_flow(self, execution_id, payload):
        try:
            anomalies = self.correlator.analyze_execution_flow(execution_id, payload)
            
            for anomaly in anomalies:
                self.anomaly_logger.log_anomaly(
                    source=anomaly.get("source"),
                    severity=anomaly.get("severity"),
                    details=anomaly.get("details"),
                    telemetry_snapshot=anomaly.get("telemetry_snapshot")
                )
                
            return self.anomaly_logger.get_structured_report()
        except Exception as e:
            if isinstance(e, AnomalyReportAggregatorError):
                raise
            raise AnomalyReportAggregatorError(str(e))

    def generate_final_report(self):
        try:
            return self.anomaly_logger.get_structured_report()
        except Exception as e:
            raise AnomalyReportAggregatorError(str(e))