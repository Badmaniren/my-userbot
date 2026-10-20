from skills.anomaly_filter import AnomalyFilter
from skills.anomaly_detector import AnomalyDetector


class AnomalyPipelineError(Exception):
    """Custom exception for anomaly pipeline errors."""
    pass


class AnomalyPipeline:
    def __init__(self, repo_path=None, threshold=None):
        self.repo_path = repo_path
        self.threshold = threshold
        
        # Инициализация свитков фильтра и детектора с поддержкой различных комбинаций аргументов
        try:
            if repo_path is not None:
                try:
                    self.filter_module = AnomalyFilter(repo_path=repo_path)
                except TypeError:
                    self.filter_module = AnomalyFilter()
            else:
                self.filter_module = AnomalyFilter()
        except TypeError:
            self.filter_module = AnomalyFilter()

        try:
            if repo_path is not None and threshold is not None:
                try:
                    self.detector_module = AnomalyDetector(repo_path=repo_path, threshold=threshold)
                except TypeError:
                    try:
                        self.detector_module = AnomalyDetector(threshold=threshold)
                    except TypeError:
                        self.detector_module = AnomalyDetector(repo_path=repo_path)
            elif threshold is not None:
                try:
                    self.detector_module = AnomalyDetector(threshold=threshold)
                except TypeError:
                    self.detector_module = AnomalyDetector()
            elif repo_path is not None:
                try:
                    self.detector_module = AnomalyDetector(repo_path=repo_path)
                except TypeError:
                    self.detector_module = AnomalyDetector()
            else:
                self.detector_module = AnomalyDetector()
        except TypeError:
            try:
                self.detector_module = AnomalyDetector()
            except TypeError:
                self.detector_module = AnomalyDetector(threshold=threshold)

    def _filter_and_extract_metrics(self, raw_data):
        try:
            filtered = self.filter_module.filter(raw_data)
        except (KeyError, TypeError, ValueError) as e:
            if isinstance(raw_data, dict):
                filtered = raw_data
            else:
                raise AnomalyPipelineError(str(e)) from e
        except Exception as e:
            raise AnomalyPipelineError(str(e)) from e

        if isinstance(filtered, dict):
            telemetry = filtered.get("telemetry_snapshot")
            if isinstance(telemetry, dict) and telemetry:
                return telemetry
            return filtered
        return filtered

    def _detect_anomaly_safe(self, metric_name, value):
        try:
            val_float = float(value)
        except (TypeError, ValueError):
            val_float = value

        if hasattr(self.detector_module, "record_metric"):
            try:
                self.detector_module.record_metric(metric_name, val_float)
            except Exception:
                pass

        try:
            return self.detector_module.detect_anomaly(metric_name, val_float)
        except Exception as e:
            raise AnomalyPipelineError(str(e)) from e

    def run(self, raw_input):
        metrics_data = self._filter_and_extract_metrics(raw_input)

        if not isinstance(metrics_data, dict) or not metrics_data:
            return {"is_anomaly": False}

        metric_name, target_val = next(iter(metrics_data.items()))

        is_anomaly = self._detect_anomaly_safe(metric_name, target_val)

        return {
            "is_anomaly": is_anomaly,
            "metric_name": metric_name,
            "target_value": target_val
        }

    def run_batch(self, raw_batch_data):
        metrics_data = self._filter_and_extract_metrics(raw_batch_data)

        results = {}
        if isinstance(metrics_data, dict):
            for metric_name, target_val in metrics_data.items():
                is_anomaly = self._detect_anomaly_safe(metric_name, target_val)
                results[metric_name] = is_anomaly

        return results

    def process_pipeline(self, raw_data):
        try:
            metrics_data = self._filter_and_extract_metrics(raw_data)
        except Exception:
            metrics_data = raw_data

        detection_output = {}
        if isinstance(metrics_data, dict):
            for k, v in metrics_data.items():
                if isinstance(v, list):
                    for val in v:
                        try:
                            detection_output[k] = self._detect_anomaly_safe(k, val)
                        except Exception:
                            detection_output[k] = False
                else:
                    try:
                        detection_output[k] = self._detect_anomaly_safe(k, v)
                    except Exception:
                        detection_output[k] = False
        
        return {
            "filtered_data": metrics_data,
            "detection_result": detection_output
        }

    def run_end_to_end(self, execution_id, metrics_payload):
        results = {}
        if isinstance(metrics_payload, dict):
            for m_name, m_val in metrics_payload.items():
                try:
                    is_anom = self._detect_anomaly_safe(m_name, m_val)
                except Exception:
                    is_anom = False
                results[m_name] = is_anom
        return results
