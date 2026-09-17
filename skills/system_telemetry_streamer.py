import time
import requests

class SystemTelemetryStreamer:
    """Модуль для сбора и потоковой передачи системной телеметрии в реальном времени."""

    def generate_payload(self, metric_name: str, value: float, host: str) -> dict:
        return {
            "metric_name": metric_name,
            "value": value,
            "host": host,
            "timestamp": time.time()
        }

    def stream_metric(self, endpoint: str, metric_name: str, value: float, host: str) -> bool:
        payload = self.generate_payload(metric_name, value, host)
        try:
            response = requests.post(endpoint, json=payload)
            if response.status_code in (200, 201, 202):
                return True
            return False
        except Exception:
            return False

    def stream_batch(self, endpoint: str, batch: list) -> bool:
        try:
            response = requests.post(endpoint, json=batch)
            if response.status_code in (200, 201, 202):
                return True
            return False
        except Exception:
            return False


def system_telemetry_streamer(payload: dict = None, **kwargs) -> dict:
    """Функция для интеграционных тестов, обрабатывающая пейлоуд телеметрии."""
    if payload is None:
        merged = kwargs
    elif isinstance(payload, dict):
        merged = {**payload, **kwargs}
    else:
        merged = {"data": payload, **kwargs}
    stream_id = merged.get("stream_id", "default-stream")
    return {
        "status": "success",
        "stream_id": stream_id,
        "processed_at": time.time()
    }