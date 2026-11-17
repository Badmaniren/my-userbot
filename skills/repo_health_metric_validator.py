import json
import requests
from typing import Dict, Any, List, Union, IO


class MetricValidationError(Exception):
    """Исключение, выбрасываемое при ошибке валидации метрик здоровья репозитория."""
    pass


class RepoHealthMetricValidator:
    """Класс для проверки валидности и корректности собранных метрик здоровья репозитория."""

    def validate(self, metric: Dict[str, Any]) -> bool:
        if not isinstance(metric, dict):
            raise MetricValidationError("Metric must be a dictionary")
        
        required_fields = ["metric_name", "score", "timestamp"]
        for field in required_fields:
            if field not in metric:
                raise MetricValidationError(f"Missing required field: {field}")
        
        score = metric["score"]
        if not isinstance(score, (int, float)) or not (0.0 <= score <= 100.0):
            raise MetricValidationError(f"Invalid score value: {score}")
            
        return True

    def validate_stream(self, stream: Union[IO[bytes], IO[str], str, bytes]) -> List[Dict[str, Any]]:
        try:
            if isinstance(stream, bytes):
                content = stream.decode('utf-8')
            elif hasattr(stream, 'read'):
                content = stream.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
            else:
                content = str(stream)
            
            data = json.loads(content)
        except (UnicodeDecodeError, json.JSONDecodeError, Exception) as e:
            raise MetricValidationError(f"Failed to parse stream: {e}")

        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            raise MetricValidationError("Stream content must be a JSON array or object")

        validated_metrics = []
        for item in data:
            self.validate(item)
            validated_metrics.append(item)

        return validated_metrics

    def dispatch_and_validate_remote(self, metric: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
        self.validate(metric)
        response = requests.post(endpoint, json=metric)
        return response.json()


def audit_repository(metric: Dict[str, Any]) -> Dict[str, Any]:
    validator = RepoHealthMetricValidator()
    validator.validate(metric)
    return metric


def render_health_dashboard(metric: Dict[str, Any]) -> str:
    name = metric.get("metric_name", "Unknown")
    score = metric.get("score", 0.0)
    return f"Dashboard - Metric: {name}, Score: {score}"


def validate_repo_health_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {"is_valid": False, "metrics": payload}
        
    working_payload = payload.copy()
    if "run_id" in working_payload and "metric_name" not in working_payload:
        working_payload["metric_name"] = working_payload["run_id"]
    if "health_score" in working_payload and "score" not in working_payload:
        working_payload["score"] = working_payload["health_score"]

    validator = RepoHealthMetricValidator()
    try:
        validator.validate(working_payload)
        return {"is_valid": True, "metrics": working_payload}
    except MetricValidationError:
        return {"is_valid": False, "metrics": payload}