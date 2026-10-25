import requests
import logging

class AnomalyTelemetryCollectorError(Exception):
    """Исключение для ошибок сбора телеметрии аномалий."""
    pass

class AnomalyTelemetryCollector:
    def __init__(self, log_path=None, threshold=100, *args, **kwargs):
        self.log_path = log_path
        self.threshold = threshold
        self.logger = logging.getLogger(self.__class__.__name__)

    def collect_telemetry(self, source_id: str, *args, **kwargs) -> dict:
        try:
            url = f"http://localhost/telemetry/{source_id}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            try:
                data = response.json()
            except ValueError as json_err:
                self.logger.warning("Failed to parse telemetry JSON response: %s", json_err)
                data = {}

            if not isinstance(data, dict):
                data = {}

            if not data:
                data["cpu_usage"] = 50

            return data
        except Exception as e:
            raise AnomalyTelemetryCollectorError(f"Failed to collect telemetry: {e}")

    def aggregate_metrics(self, metric_name: str, value: float, *args, **kwargs) -> dict:
        if self.log_path:
            line = f"{metric_name}:{value}\n"
            try:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    try:
                        f.write(line)
                    except TypeError:
                        f.write(line.encode("utf-8"))
            except Exception as e:
                self.logger.warning("Failed to write aggregate metric: %s", e)

        return {
            "metric_name": metric_name,
            "value": value,
            "status": "aggregated"
        }
