from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError
from skills.anomaly_logger import AnomalyLogger


class AnomalyCorrelatorError(Exception):
    """Кастомное исключение для ошибок модуля AnomalyCorrelator."""
    pass


class AnomalyCorrelator:
    def __init__(self, repo_path=None, log_path=None, threshold=None, detector=None, logger=None):
        if detector is not None:
            self.detector = detector
        else:
            kwargs = {}
            if threshold is not None:
                kwargs['threshold'] = threshold
            kwargs['git_inspector'] = None
            kwargs['patch_verifier'] = None
            self.detector = AnomalyDetector(repo_path=repo_path, **kwargs)

        if logger is not None:
            self.logger = logger
        else:
            self.logger = AnomalyLogger(log_path=log_path or "/tmp/anomaly_correlator.log")

    def correlate_metric(self, metric_name, value):
        try:
            self.detector.record_metric(metric_name, value)
            is_anomaly = self.detector.detect_anomaly(metric_name, value)
            if is_anomaly:
                self.logger.log_anomaly(metric_name)
            return is_anomaly
        except AnomalyDetectorError as e:
            raise AnomalyCorrelatorError(str(e)) from e

    def analyze_execution_flow(self, execution_id, metrics_payload):
        return self.detector.analyze_execution_metrics(execution_id, metrics_payload)

    def get_correlation_report(self):
        return self.logger.get_structured_report()

    def correlate_events(self):
        anomalies = self.logger.get_anomalies()
        report = self.logger.get_structured_report()
        return {
            "correlated_count": len(anomalies),
            "report": report
        }