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

    def aggregate_and_report(self, metric_name, value):
        try:
            self.correlator.correlate_metric(metric_name, value)
            anomalies = self.correlator.correlate_events()
            
            if isinstance(anomalies, dict):
                events = anomalies.get("events", anomalies.get("report", []))
            elif isinstance(anomalies, list):
                events = anomalies
            else:
                events = []

            for anomaly in events:
                if isinstance(anomaly, dict):
                    self.anomaly_logger.log_anomaly(
                        source=anomaly.get("source"),
                        severity=anomaly.get("severity"),
                        details=anomaly.get("details"),
                        telemetry_snapshot=anomaly.get("telemetry_snapshot")
                    )
                elif isinstance(anomaly, str):
                    self.anomaly_logger.log_anomaly(
                        source="correlator",
                        details={"message": anomaly}
                    )
                
            return self.anomaly_logger.get_structured_report()
        except AnomalyCorrelatorError as e:
            raise AnomalyReportAggregatorError(str(e))

    def aggregate_execution_flow(self, execution_id, payload):
        try:
            anomalies = self.correlator.analyze_execution_flow(execution_id, payload)
            
            if isinstance(anomalies, dict):
                events = anomalies.get("events", anomalies.get("report", []))
            elif isinstance(anomalies, list):
                events = anomalies
            else:
                events = []

            for anomaly in events:
                if isinstance(anomaly, dict):
                    self.anomaly_logger.log_anomaly(
                        source=anomaly.get("source"),
                        severity=anomaly.get("severity"),
                        details=anomaly.get("details"),
                        telemetry_snapshot=anomaly.get("telemetry_snapshot")
                    )
                elif isinstance(anomaly, str):
                    self.anomaly_logger.log_anomaly(
                        source="correlator",
                        details={"message": anomaly}
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