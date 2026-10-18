from skills.anomaly_filter import AnomalyFilter
from skills.anomaly_detector import AnomalyDetector
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger


class AnomalyPipelineError(Exception):
    """Custom exception for anomaly pipeline errors."""
    pass


class AnomalyPipeline:
    def __init__(
        self,
        repo_path=None,
        threshold=None,
        log_path=None,
        audit_hub=None,
        logger=None,
        anomaly_filter=None,
        anomaly_detector=None
    ):
        self.repo_path = repo_path
        self.threshold = threshold
        self.log_path = log_path
        self.audit_hub = audit_hub
        self.logger = logger
        
        if anomaly_filter is not None:
            self.filter_module = anomaly_filter
        else:
            try:
                self.filter_module = AnomalyFilter()
            except TypeError:
                self.filter_module = AnomalyFilter(repo_path=repo_path)

        if anomaly_detector is not None:
            self.detector_module = anomaly_detector
        else:
            try:
                self.detector_module = AnomalyDetector(repo_path=repo_path, threshold=threshold)
            except TypeError:
                try:
                    self.detector_module = AnomalyDetector(threshold=threshold)
                except TypeError:
                    self.detector_module = AnomalyDetector()

        if self.audit_hub is None and log_path is not None:
            try:
                self.audit_hub = AnomalyAuditHub(
                    repo_path=repo_path or ".",
                    log_path=log_path,
                    threshold=threshold or 5.0
                )
            except Exception:
                self.audit_hub = None

        if self.logger is None and log_path is not None:
            try:
                self.logger = AnomalyLogger(log_path=log_path)
            except Exception:
                self.logger = None

    def run(self, raw_input):
        try:
            filtered = self.filter_module.filter(raw_input)
        except Exception as e:
            raise AnomalyPipelineError(str(e)) from e

        if not isinstance(filtered, dict) or not filtered:
            return {"is_anomaly": False}

        metric_name, target_val = next(iter(filtered.items()))

        try:
            if hasattr(self.detector_module, "record_metric"):
                self.detector_module.record_metric(metric_name, float(target_val))
            is_anomaly = self.detector_module.detect_anomaly(metric_name, target_val)
        except Exception as e:
            raise AnomalyPipelineError(str(e)) from e

        return {
            "is_anomaly": is_anomaly,
            "metric_name": metric_name,
            "target_value": target_val
        }

    def run_batch(self, raw_batch_data):
        try:
            filtered = self.filter_module.filter(raw_batch_data)
        except Exception as e:
            if isinstance(raw_batch_data, dict):
                filtered = raw_batch_data
            else:
                raise AnomalyPipelineError(str(e)) from e

        results = {}
        if isinstance(filtered, dict):
            for metric_name, target_val in filtered.items():
                try:
                    if hasattr(self.detector_module, "record_metric"):
                        self.detector_module.record_metric(metric_name, float(target_val))
                    is_anomaly = self.detector_module.detect_anomaly(metric_name, float(target_val))
                except Exception:
                    is_anomaly = False
                results[metric_name] = is_anomaly

        return results

    def process_pipeline(self, raw_data):
        try:
            filtered = self.filter_module.filter(raw_data)
        except Exception:
            filtered = raw_data

        detection_output = {}
        if isinstance(filtered, dict):
            for k, v in filtered.items():
                if isinstance(v, list):
                    for val in v:
                        try:
                            if hasattr(self.detector_module, "record_metric"):
                                self.detector_module.record_metric(k, float(val))
                            detection_output[k] = self.detector_module.detect_anomaly(k, float(val))
                        except Exception:
                            detection_output[k] = False
                else:
                    try:
                        if hasattr(self.detector_module, "record_metric"):
                            self.detector_module.record_metric(k, float(v))
                        detection_output[k] = self.detector_module.detect_anomaly(k, float(v))
                    except Exception:
                        detection_output[k] = False
        
        return {
            "filtered_data": filtered,
            "detection_result": detection_output
        }

    def run_end_to_end(self, execution_id, metrics_payload):
        results = {}
        if isinstance(metrics_payload, dict):
            for m_name, m_val in metrics_payload.items():
                try:
                    if hasattr(self.detector_module, "record_metric"):
                        self.detector_module.record_metric(m_name, float(m_val))
                    is_anom = self.detector_module.detect_anomaly(m_name, float(m_val))
                except Exception:
                    is_anom = False
                results[m_name] = is_anom
        return results
