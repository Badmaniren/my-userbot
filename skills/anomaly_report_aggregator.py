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

    def _extract_and_log_anomalies(self, anomalies, default_source=None):
        if isinstance(anomalies, dict):
            if "anomalies" in anomalies and isinstance(anomalies["anomalies"], list):
                events = anomalies["anomalies"]
            elif "anomalies_detected" in anomalies and isinstance(anomalies["anomalies_detected"], list):
                events = anomalies["anomalies_detected"]
            elif "events" in anomalies and isinstance(anomalies["events"], list):
                events = anomalies["events"]
            elif any(k in anomalies for k in ("source", "severity", "details", "telemetry_snapshot")):
                events = [anomalies]
            else:
                events = []
        elif isinstance(anomalies, list):
            events = anomalies
        elif isinstance(anomalies, str):
            events = [anomalies]
        else:
            events = []

        for anomaly in events:
            if isinstance(anomaly, dict):
                self.anomaly_logger.log_anomaly(
                    source=anomaly.get("source", default_source),
                    severity=anomaly.get("severity"),
                    details=anomaly.get("details"),
                    telemetry_snapshot=anomaly.get("telemetry_snapshot")
                )
            elif isinstance(anomaly, str):
                self.anomaly_logger.log_anomaly(
                    source=default_source or anomaly,
                    details={"info": anomaly}
                )

    def aggregate_and_report(self, metric_name, value):
        try:
            self.correlator.correlate_metric(metric_name, value)
            anomalies = self.correlator.correlate_events()
            self._extract_and_log_anomalies(anomalies, default_source=metric_name)
            return self.anomaly_logger.get_structured_report()
        except AnomalyCorrelatorError as e:
            raise AnomalyReportAggregatorError(str(e))

    def aggregate_execution_flow(self, execution_id, payload):
        try:
            anomalies = self.correlator.analyze_execution_flow(execution_id, payload)
            self._extract_and_log_anomalies(anomalies, default_source=execution_id)
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