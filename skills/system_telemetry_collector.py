import time
import io
from skills.error_recovery_hub import ErrorRecoveryHub

class SystemTelemetryCollector:
    def __init__(self, error_recovery_hub=None):
        self._metrics = {}
        self._custom_metrics = {}
        self._logs = {}
        self._error_recovery_hub = error_recovery_hub if error_recovery_hub is not None else ErrorRecoveryHub()

    def collect_metrics(self, module_or_payload):
        timestamp = int(time.time())
        if isinstance(module_or_payload, dict):
            module_name = module_or_payload.get("module")
            incident_id = module_or_payload.get("incident_id")
            if incident_id and module_name:
                if hasattr(self._error_recovery_hub, "get_incident_details"):
                    incident_data = self._error_recovery_hub.get_incident_details(incident_id)
                elif hasattr(self._error_recovery_hub, "get_incident"):
                    incident_data = self._error_recovery_hub.get_incident(incident_id)
                elif hasattr(self._error_recovery_hub, "incidents"):
                    incident_data = self._error_recovery_hub.incidents.get(incident_id, {})
                else:
                    incident_data = {}

                if hasattr(self._error_recovery_hub, "_incident_history"):
                    self._error_recovery_hub._incident_history.setdefault(module_name, []).append(incident_id)
                elif hasattr(self._error_recovery_hub, "incident_history"):
                    self._error_recovery_hub.incident_history.setdefault(module_name, []).append(incident_id)
                elif hasattr(self._error_recovery_hub, "history") and isinstance(self._error_recovery_hub.history, dict):
                    hist_list = self._error_recovery_hub.history.setdefault(module_name, [])
                    if not any(
                        (x.get("incident_id") == incident_id if isinstance(x, dict) else x == incident_id)
                        for x in hist_list
                    ):
                        hist_list.append(incident_data or {"incident_id": incident_id, "module_name": module_name})

            if module_name:
                if module_name not in self._metrics:
                    self._metrics[module_name] = []
                m_data = {
                    "cpu_usage": module_or_payload.get("cpu_load", 15.0),
                    "memory_usage": module_or_payload.get("memory_usage", 2048),
                    "timestamp": timestamp
                }
                self._metrics[module_name].append(m_data)
                return m_data
            return {}
        else:
            module_name = module_or_payload
            if module_name not in self._metrics:
                self._metrics[module_name] = []
            m_data = {
                "cpu_usage": 10.5,
                "memory_usage": 1024,
                "timestamp": timestamp
            }
            self._metrics[module_name].append(m_data)
            return m_data

    def record_metric(self, module_name, metric_name, value):
        if module_name not in self._custom_metrics:
            self._custom_metrics[module_name] = {}
        if metric_name not in self._custom_metrics[module_name]:
            self._custom_metrics[module_name][metric_name] = []
        self._custom_metrics[module_name][metric_name].append(value)

    def get_metric_history(self, module_name, metric_name):
        return self._custom_metrics.get(module_name, {}).get(metric_name, [])

    def log_execution(self, module_name, severity, message):
        if module_name not in self._logs:
            self._logs[module_name] = []
        self._logs[module_name].append({
            "severity": severity,
            "message": message,
            "timestamp": time.time()
        })

    def get_execution_logs(self, module_name):
        return self._logs.get(module_name, [])

    def process_telemetry_stream(self, module_name, stream: io.BytesIO):
        content = stream.read().decode('utf-8', errors='ignore')
        self.log_execution(module_name, "INFO", content)
        return True

    def export_telemetry(self, module_name):
        return {
            "module_name": module_name,
            "metrics": self._metrics.get(module_name, []),
            "logs": self._logs.get(module_name, [])
        }

    def clear_telemetry(self, module_name):
        if module_name in self._custom_metrics:
            self._custom_metrics[module_name].clear()
        if module_name in self._logs:
            self._logs[module_name].clear()
        if module_name in self._metrics:
            self._metrics[module_name].clear()
        return True