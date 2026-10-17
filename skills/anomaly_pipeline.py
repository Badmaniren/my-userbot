from skills.anomaly_filter import AnomalyFilter
from skills.anomaly_detector import AnomalyDetector


class AnomalyPipelineError(Exception):
    """Исключение, возникающее в процессе работы конвейера аномалий."""
    pass


class AnomalyPipeline:
    def __init__(self, repo_path=None, threshold=None, anomaly_filter=None, anomaly_detector=None):
        self.anomaly_filter = anomaly_filter if anomaly_filter is not None else AnomalyFilter()

        if anomaly_detector is not None:
            self.anomaly_detector = anomaly_detector
        else:
            self.anomaly_detector = AnomalyDetector(
                repo_path=repo_path,
                threshold=threshold,
                git_inspector=None,
                patch_verifier=None
            )

    def _prepare_payload(self, raw_item):
        if not isinstance(raw_item, dict):
            return raw_item
        required = ("source", "severity", "details", "telemetry_snapshot")
        if all(k in raw_item for k in required):
            return raw_item
        if "metric" in raw_item or "value" in raw_item:
            payload = dict(raw_item)
            if "source" not in payload:
                payload["source"] = payload.get("metric", "telemetry_source")
            if "severity" not in payload:
                payload["severity"] = "LOW"
            if "details" not in payload:
                payload["details"] = f"Metric {payload.get('metric')} payload"
            if "telemetry_snapshot" not in payload:
                payload["telemetry_snapshot"] = {"value": payload.get("value")} if "value" in payload else {}
            return payload
        return raw_item

    def process_telemetry(self, input_payload):
        try:
            payload = self._prepare_payload(input_payload)
            filtered_data = self.anomaly_filter.filter(payload)
            if filtered_data is None:
                return None

            metric_name = filtered_data.get("metric") or (input_payload.get("metric") if isinstance(input_payload, dict) else None)
            value = filtered_data.get("value") if (isinstance(filtered_data, dict) and "value" in filtered_data) else (input_payload.get("value") if isinstance(input_payload, dict) else None)

            self.anomaly_detector.record_metric(metric_name, value)
            is_anomaly = self.anomaly_detector.detect_anomaly(metric_name, value)

            return {
                "is_anomaly": is_anomaly,
                "metric_name": metric_name,
                "target_value": value
            }
        except Exception as e:
            if isinstance(e, AnomalyPipelineError):
                raise e
            raise AnomalyPipelineError(str(e))

    def process(self, raw_data_list):
        filtered_results = []
        detection_results = []

        for item in raw_data_list:
            try:
                payload = self._prepare_payload(item)
                filtered = self.anomaly_filter.filter(payload)
            except Exception as e:
                raise AnomalyPipelineError(str(e))

            if filtered is not None:
                filtered_results.append(filtered)
                metric_name = filtered.get("metric") or (item.get("metric") if isinstance(item, dict) else None)
                value = filtered.get("value") if (isinstance(filtered, dict) and "value" in filtered) else (item.get("value") if isinstance(item, dict) else None)

                try:
                    self.anomaly_detector.record_metric(metric_name, value)
                    is_anomaly = self.anomaly_detector.detect_anomaly(metric_name, value)
                except Exception as e:
                    raise AnomalyPipelineError(str(e))

                detection_results.append({
                    "is_anomaly": is_anomaly,
                    "metric_name": metric_name,
                    "target_value": value
                })

        return {
            "filtered_data": filtered_results,
            "detection_results": detection_results
        }