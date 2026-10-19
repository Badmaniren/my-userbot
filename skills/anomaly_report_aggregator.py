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

    def _log_anomaly(self, anomaly):
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
                severity="MEDIUM",
                details={"message": anomaly},
                telemetry_snapshot=None
            )
        else:
            source = getattr(anomaly, "source", str(anomaly))
            severity = getattr(anomaly, "severity", "MEDIUM")
            details = getattr(anomaly, "details", None)
            telemetry_snapshot = getattr(anomaly, "telemetry_snapshot", None)
            self.anomaly_logger.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )

    def aggregate_and_report(self, metric_name, value):
        try:
            self.correlator.correlate_metric(metric_name, value)
            anomalies = self.correlator.correlate_events()
            
            if anomalies:
                for anomaly in anomalies:
                    self._log_anomaly(anomaly)
                
            return self.anomaly_logger.get_structured_report()
        except AnomalyCorrelatorError as e:
            raise AnomalyReportAggregatorError(str(e))
        except AnomalyReportAggregatorError:
            raise
        except Exception as e:
            raise AnomalyReportAggregatorError(str(e))

    def aggregate_execution_flow(self, execution_id, payload):
        try:
            if isinstance(payload, dict):
                for k, v in list(payload.items()):
                    if isinstance(v, str):
                        try:
                            payload[k] = float(v)
                        except ValueError:
                            pass

            anomalies = self.correlator.analyze_execution_flow(execution_id, payload)
            
            if anomalies:
                if isinstance(anomalies, dict):
                    detected = anomalies.get("anomalies_detected", [])
                    for item in detected:
                        self._log_anomaly({
                            "source": execution_id,
                            "severity": "HIGH",
                            "details": {"metric": item, "execution_id": execution_id},
                            "telemetry_snapshot": payload if isinstance(payload, dict) else None
                        })
                elif isinstance(anomalies, (list, tuple)):
                    for anomaly in anomalies:
                        self._log_anomaly(anomaly)
                
            return self.anomaly_logger.get_structured_report()
        except Exception as e:
            if isinstance(e, AnomalyReportAggregatorError):
                raise
            raise AnomalyReportAggregatorError(str(e))

    def generate_final_report(self):
        try:
            return self.anomaly_logger.get_structured_report()
        except Exception as e:
            if isinstance(e, AnomalyReportAggregatorError):
                raise
            raise AnomalyReportAggregatorError(str(e))