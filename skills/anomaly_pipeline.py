from skills.anomaly_filter import AnomalyFilter
from skills.anomaly_detector import AnomalyDetector


class AnomalyPipelineError(Exception):
    """Custom exception for anomaly pipeline errors."""
    pass


class AnomalyPipeline:
    def __init__(self, repo_path=None, threshold=None):
        self.repo_path = repo_path
        self.threshold = threshold
        
        try:
            self.filter_module = AnomalyFilter()
        except TypeError:
            self.filter_module = AnomalyFilter(repo_path=repo_path)
            
        try:
            self.detector_module = AnomalyDetector(repo_path=repo_path, threshold=threshold)
        except TypeError:
            try:
                self.detector_module = AnomalyDetector(threshold=threshold)
            except TypeError:
                self.detector_module = AnomalyDetector()

    def run(self, raw_input):
        try:
            filtered = self.filter_module.filter(raw_input)
        except Exception as e:
            raise AnomalyPipelineError(str(e)) from e

        if not isinstance(filtered, dict) or not filtered:
            return {"is_anomaly": False}

        metric_name, target_val = next(iter(filtered.items()))

        try:
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
            raise AnomalyPipelineError(str(e)) from e

        results = {}
        if isinstance(filtered, dict):
            for metric_name, target_val in filtered.items():
                try:
                    is_anomaly = self.detector_module.detect_anomaly(metric_name, target_val)
                except Exception as e:
                    raise AnomalyPipelineError(str(e)) from e
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
                            detection_output[k] = self.detector_module.detect_anomaly(k, float(val))
                        except Exception:
                            detection_output[k] = False
                else:
                    try:
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
                    is_anom = self.detector_module.detect_anomaly(m_name, float(m_val))
                except Exception:
                    is_anom = False
                results[m_name] = is_anom
        return results