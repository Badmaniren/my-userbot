import json
import io
import time
import requests
from typing import Dict, Any, List, Union


class MetricValidationError(ValueError):
    """Исключение, выбрасываемое при ошибке валидации метрик здоровья репозитория."""
    pass


class RepoHealthMetricValidator:
    """Класс для валидации метрик здоровья репозитория."""

    def validate(self, metric: Dict[str, Any]) -> bool:
        if not isinstance(metric, dict):
            raise MetricValidationError("Metric must be a dictionary")

        metric_name = metric.get("metric_name")
        score = metric.get("score")
        timestamp = metric.get("timestamp")

        if not isinstance(metric_name, str) or not metric_name:
            raise MetricValidationError("Invalid or missing 'metric_name'")

        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise MetricValidationError("Score must be a number")

        if not (0.0 <= score <= 100.0):
            raise MetricValidationError("Score must be between 0.0 and 100.0")

        if not isinstance(timestamp, int) or isinstance(timestamp, bool):
            raise MetricValidationError("Timestamp must be an integer")

        return True

    def validate_stream(self, stream: Union[io.BytesIO, io.StringIO]) -> List[Dict[str, Any]]:
        try:
            if isinstance(stream, io.BytesIO):
                raw_data = stream.read()
                try:
                    content = raw_data.decode('utf-8')
                except UnicodeDecodeError as e:
                    raise MetricValidationError(f"Failed to decode stream bytes: {e}")
            elif isinstance(stream, io.StringIO):
                content = stream.read()
            else:
                content = stream.read()
                if isinstance(content, bytes):
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError as e:
                        raise MetricValidationError(f"Failed to decode stream bytes: {e}")

            data = json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise MetricValidationError(f"Invalid JSON in stream: {e}")

        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise MetricValidationError("Stream data must be a JSON object or a list of objects")

        validated_items = []
        for item in data:
            self.validate(item)
            validated_items.append(item)

        return validated_items

    def dispatch_and_validate_remote(self, payload: Dict[str, Any], url: str) -> Dict[str, Any]:
        self.validate(payload)
        response = requests.post(url, json=payload)
        return response.json()


def validate_repo_health_metrics(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    metrics = dict(raw_data)

    if "health_score" in metrics and "score" not in metrics:
        metrics["score"] = metrics.pop("health_score")
    if "run_id" in metrics and "metric_name" not in metrics:
        metrics["metric_name"] = metrics.pop("run_id")
    if "timestamp" not in metrics:
        metrics["timestamp"] = int(time.time())

    validator = RepoHealthMetricValidator()
    try:
        validator.validate(metrics)
        is_valid = True
    except MetricValidationError:
        is_valid = False

    return {
        "is_valid": is_valid,
        "metrics": metrics
    }


def audit_repository(metrics: Dict[str, Any]) -> Dict[str, Any]:
    return metrics


def render_health_dashboard(metrics: Dict[str, Any]) -> str:
    return f"Dashboard for {metrics.get('metric_name', 'Unknown')} with score {metrics.get('score', 0.0)}"