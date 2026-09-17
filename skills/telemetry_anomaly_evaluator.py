import re
from typing import Dict, Any, List, Union
from skills import incident_aggregator
from skills import telemetry_processor

class TelemetryAnomalyEvaluator:
    def _parse_stream(self, stream: Any) -> Dict[str, Any]:
        if hasattr(stream, 'read'):
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
        elif isinstance(stream, str):
            content = stream
        elif isinstance(stream, dict):
            # Integration payload support
            return {
                "stream_id": stream.get("stream_id"),
                "metric": stream.get("metric_name") or stream.get("metric"),
                "value": stream.get("value")
            }
        else:
            content = str(stream)

        data = {}
        for line in content.splitlines():
            parts = line.split(';')
            for part in parts:
                if ':' in part:
                    k, v = part.split(':', 1)
                    k = k.strip().upper()
                    v = v.strip()
                    if k == 'STREAM_ID':
                        data['stream_id'] = v
                    elif k == 'METRIC':
                        data['metric'] = v
                    elif k == 'VALUE':
                        try:
                            data['value'] = float(v)
                        except ValueError:
                            data['value'] = v
        return data

    def evaluate_stream(self, stream: Any, threshold: float) -> Dict[str, Any]:
        parsed = self._parse_stream(stream)
        stream_id = parsed.get('stream_id')
        metric = parsed.get('metric')
        value = parsed.get('value')

        if not stream_id and not metric and value is None:
            return {
                'anomaly_detected': False,
                'stream_id': None
            }

        anomaly_detected = False
        if isinstance(value, (int, float)) and value > threshold:
            anomaly_detected = True
            if hasattr(incident_aggregator, 'report_anomaly'):
                incident_aggregator.report_anomaly(stream_id, metric, value, threshold)

        result = {
            'anomaly_detected': anomaly_detected,
            'stream_id': stream_id,
            'metric': metric,
            'metric_value': value
        }
        if anomaly_detected:
            result['breach_value'] = value
            result['incident_metric_feed'] = True

        return result

    def evaluate_batch(self, streams: List[Any], threshold: float) -> List[Dict[str, Any]]:
        results = []
        for stream in streams:
            results.append(self.evaluate_stream(stream, threshold))
        return results

    def __call__(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        processed_stream = payload.get("processed_stream")
        threshold = payload.get("threshold", 100.0)

        parsed = self._parse_stream(processed_stream)
        value = parsed.get("value")
        stream_id = parsed.get("stream_id")
        metric = parsed.get("metric")

        anomaly_detected = False
        if isinstance(value, (int, float)) and value > threshold:
            anomaly_detected = True
            if hasattr(incident_aggregator, 'report_anomaly'):
                incident_aggregator.report_anomaly(stream_id, metric, value, threshold)

        result = {
            "anomaly_detected": anomaly_detected,
            "metric_value": value,
            "incident_metric_feed": anomaly_detected,
            "stream_id": stream_id,
            "metric": metric
        }
        if anomaly_detected:
            result['breach_value'] = value

        return result

telemetry_anomaly_evaluator = TelemetryAnomalyEvaluator()