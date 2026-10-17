from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_visualizer import AnomalyVisualizer
import skills.anomaly_filter as anomaly_filter_module


class AnomalyCorrelatorError(Exception):
    """Кастомное исключение для ошибок модуля AnomalyCorrelator."""
    pass


class AnomalyCorrelator:
    def __init__(
        self,
        repo_path=None,
        log_path=None,
        threshold=None,
        detector=None,
        logger=None,
        filter_instance=None,
        visualizer=None
    ):
        try:
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
                self.logger = AnomalyLogger(log_path=log_path)

            self.filter_instance = filter_instance
            if visualizer is not None:
                self.visualizer = visualizer
            else:
                self.visualizer = AnomalyVisualizer()
        except Exception as e:
            raise AnomalyCorrelatorError(f"Initialization error: {e}") from e

    def correlate(self, raw_data):
        try:
            if self.filter_instance is not None:
                if hasattr(self.filter_instance, 'filter'):
                    filtered_data = self.filter_instance.filter(raw_data)
                elif callable(self.filter_instance):
                    filtered_data = self.filter_instance(raw_data)
                else:
                    filtered_data = anomaly_filter_module.start_new(raw_data)
            else:
                filtered_data = anomaly_filter_module.start_new(raw_data)

            source = filtered_data.get("source", "unknown")
            severity = filtered_data.get("severity", "LOW")
            details = filtered_data.get("details", {})
            telemetry_snapshot = filtered_data.get("telemetry_snapshot", {})

            # Record metrics from telemetry_snapshot if present
            if isinstance(telemetry_snapshot, dict):
                for metric_name, val in telemetry_snapshot.items():
                    if isinstance(val, (int, float)):
                        self.detector.record_metric(metric_name, float(val))

            self.logger.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )

            anomalies = self.logger.get_anomalies()
            report = self.logger.get_structured_report()
            visualization = self.visualizer.visualize_digest(report)

            return {
                "filtered_data": filtered_data,
                "correlated_count": len(anomalies),
                "report": report,
                "visualization": visualization
            }
        except Exception as e:
            if isinstance(e, AnomalyCorrelatorError):
                raise
            raise AnomalyCorrelatorError(f"Error during anomaly correlation: {e}") from e

    def correlate_metric(self, metric_name, value):
        try:
            self.detector.record_metric(metric_name, value)
            is_anomaly = self.detector.detect_anomaly(metric_name, value)
            if is_anomaly:
                self.logger.log_anomaly(metric_name)
            return is_anomaly
        except Exception as e:
            if isinstance(e, AnomalyCorrelatorError):
                raise
            raise AnomalyCorrelatorError(str(e)) from e

    def analyze_execution_flow(self, execution_id, metrics_payload):
        try:
            return self.detector.analyze_execution_metrics(execution_id, metrics_payload)
        except Exception as e:
            if isinstance(e, AnomalyCorrelatorError):
                raise
            raise AnomalyCorrelatorError(str(e)) from e

    def get_correlation_report(self):
        try:
            return self.logger.get_structured_report()
        except Exception as e:
            if isinstance(e, AnomalyCorrelatorError):
                raise
            raise AnomalyCorrelatorError(str(e)) from e

    def correlate_events(self):
        try:
            anomalies = self.logger.get_anomalies()
            report = self.logger.get_structured_report()
            return {
                "correlated_count": len(anomalies),
                "report": report
            }
        except Exception as e:
            if isinstance(e, AnomalyCorrelatorError):
                raise
            raise AnomalyCorrelatorError(str(e)) from e