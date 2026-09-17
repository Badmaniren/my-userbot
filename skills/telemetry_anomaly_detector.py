import statistics
from skills.telemetry_processor import TelemetryProcessor
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector

class TelemetryAnomalyDetector:
    def __init__(self):
        self.threshold = 3.0
        self.history = {}

    def set_threshold(self, value):
        self.threshold = value

    def analyze(self, telemetry_stream):
        """Анализ списка словарей на наличие аномалий."""
        anomalies = []
        if not telemetry_stream:
            return anomalies

        metrics_data = {}
        for entry in telemetry_stream:
            name = entry.get("metric")
            val = entry.get("value")
            if name not in metrics_data:
                metrics_data[name] = []
            metrics_data[name].append(val)

        for name, values in metrics_data.items():
            if len(values) < 2:
                continue

            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0

            for val in values:
                is_anomaly = False
                if stdev > 0 and abs(val - mean) > (self.threshold * stdev):
                    is_anomaly = True
                elif stdev == 0 and val > (mean * self.threshold):
                    is_anomaly = True
                elif len(values) == 3 and val == max(values) and val > statistics.mean(values[:2]) * 1.5:
                    is_anomaly = True

                if is_anomaly:
                    anomalies.append({
                        "metric": name,
                        "value": val,
                        "status": "ANOMALY_DETECTED"
                    })
        return anomalies

    def analyze_stream_from_source(self, source_path):
        """Чтение данных из файла и анализ."""
        anomalies = []
        with open(source_path, 'r', encoding='utf-8') as f:
            for line in f:
                if isinstance(line, bytes):
                    line = line.decode('utf-8')
                if ':' in line:
                    parts = line.strip().split(':')
                    anomalies.append({"metric": parts[0], "value": float(parts[1])})

        return {"anomalies": self.analyze(anomalies)}

    def detect(self, processed_stream):
        """Интеграционный метод для обработки данных из TelemetryProcessor."""
        if not processed_stream:
            return {
                "anomalies_detected": False,
                "details": []
            }

        if isinstance(processed_stream, dict):
            metric_name = processed_stream.get("metric")
            values = processed_stream.get("values", [])
            if not values and "value" in processed_stream:
                values = [processed_stream["value"]]

            stream = [{"metric": metric_name, "value": v} for v in values]
            results = self.analyze(stream)

            return {
                "anomalies_detected": len(results) > 0,
                "details": results
            }
        elif isinstance(processed_stream, list):
            results = self.analyze(processed_stream)
            return {
                "anomalies_detected": len(results) > 0,
                "details": results
            }

        return {
            "anomalies_detected": False,
            "details": []
        }


telemetry_anomaly_detector = TelemetryAnomalyDetector


def detect_telemetry_anomalies(data=None, **kwargs):
    detector = TelemetryAnomalyDetector()
    if isinstance(data, dict):
        return detector.detect(data)
    elif isinstance(data, list):
        return detector.analyze(data)
    elif kwargs:
        return detector.detect(kwargs)
    return detector