import json
import requests
from typing import Dict, Any, List, Union, IO


class MetricValidationError(Exception):
    """Исключение, выбрасываемое при ошибке валидации метрик здоровья репозитория."""
    pass


class RepoHealthMetricValidator:
    """Класс для проверки валидности и корректности собранных метрик здоровья репозитория."""

    def __init__(self):
        pass

    def validate(self, metric_data: Dict[str, Any]) -> bool:
        """Проверяет отдельный словарь с метрикой на наличие обязательных полей и корректность значений."""
        if not isinstance(metric_data, dict):
            raise MetricValidationError("Metric data must be a dictionary.")

        # Проверяем обязательные поля
        if "metric_name" not in metric_data:
            raise MetricValidationError("Missing mandatory field: 'metric_name'")
        if "score" not in metric_data:
            raise MetricValidationError("Missing mandatory field: 'score'")
        if "timestamp" not in metric_data:
            raise MetricValidationError("Missing mandatory field: 'timestamp'")

        score = metric_data["score"]
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise MetricValidationError("Score must be a number.")

        if score < 0.0 or score > 100.0:
            raise MetricValidationError(f"score is out of bounds [0.0, 100.0]. Value: {score}")

        return True

    def validate_stream(self, stream: Union[IO[bytes], IO[str], str, bytes]) -> List[Dict[str, Any]]:
        """Читает поток данных (стрим), парсит JSON и валидирует каждую метрику."""
        if hasattr(stream, "read"):
            content = stream.read()
        else:
            content = stream

        if isinstance(content, bytes):
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError as e:
                raise MetricValidationError(f"Failed to decode stream bytes: {e}")

        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError) as e:
            raise MetricValidationError(f"Failed to parse JSON: {e}")

        if not isinstance(data, list):
            data = [data]

        validated_metrics = []
        for item in data:
            self.validate(item)
            validated_metrics.append(item)

        return validated_metrics

    def dispatch_and_validate_remote(self, payload: Dict[str, Any], endpoint_url: str) -> Dict[str, Any]:
        """Отправляет метрики на внешний шлюз и возвращает ответ."""
        response = requests.post(endpoint_url, json=payload)
        return response.json()


def audit_repository(metrics_data: Dict[str, Any]) -> Dict[str, Any]:
    """Аудит репозитория, возвращает переданные метрики."""
    return metrics_data


def render_health_dashboard(metrics_data: Dict[str, Any]) -> str:
    """Рендеринг дэшборда, возвращает строку-путь или описание."""
    return "dashboard_output.html"


def validate_repo_health_metrics(metrics_data: Dict[str, Any]) -> Dict[str, Any]:
    """Интеграционная обертка для валидации метрик для дашборда и аудитора."""
    validator = RepoHealthMetricValidator()

    normalized_data = dict(metrics_data)
    if "health_score" in normalized_data and "score" not in normalized_data:
        normalized_data["score"] = normalized_data["health_score"]
    if "run_id" in normalized_data and "metric_name" not in normalized_data:
        normalized_data["metric_name"] = normalized_data["run_id"]
    if "timestamp" not in normalized_data:
        normalized_data["timestamp"] = 1600000000

    try:
        validator.validate(normalized_data)
        is_valid = True
    except MetricValidationError:
        is_valid = False

    return {
        "is_valid": is_valid,
        "metrics": normalized_data
    }