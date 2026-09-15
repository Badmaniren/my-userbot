import json
import requests

class SystemTelemetryCollector:
    def collect_and_send(self, endpoint, module_name, metric_type, value):
        payload = {
            "module": module_name,
            "metric": metric_type,
            "value": value
        }
        try:
            response = requests.post(endpoint, json=payload)
            if response.status_code == 200:
                return True
            return False
        except Exception:
            return False

    def aggregate_metrics_from_stream(self, stream):
        try:
            content = stream.read()
            data = json.loads(content.decode('utf-8'))
            if not isinstance(data, list):
                raise ValueError("Not a list")

            total = len(data)
            resolved = sum(1 for item in data if item.get("resolved") is True)
            critical = sum(1 for item in data if item.get("severity") == "CRITICAL")

            return {
                "total_incidents": total,
                "resolved_count": resolved,
                "critical_count": critical
            }
        except Exception:
            return {
                "total_incidents": 0,
                "parse_error": True
            }

    def export_report(self, report_payload, file_path):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json.dumps(report_payload))
            return True
        except Exception:
            return False

    def __call__(self, payload):
        return {"status": "success", "payload": payload}

    def collect_metrics(self, payload):
        return self.__call__(payload)

    def record_telemetry(self, payload):
        return self.__call__(payload)

    def send_telemetry(self, payload):
        return self.__call__(payload)