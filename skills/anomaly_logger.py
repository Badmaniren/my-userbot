import json
import os
import uuid
from skills.system_telemetry import SystemTelemetry, SystemTelemetryError


class AnomalyLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path

    def _get_target_path(self):
        if self.log_path and os.path.isdir(self.log_path):
            return os.path.join(self.log_path, "anomalies.log")
        return self.log_path

    def log_anomaly(self, source=None, severity=None, details=None, telemetry_snapshot=None):
        if isinstance(source, dict):
            anomaly_data = source.copy()
            if telemetry_snapshot is not None:
                anomaly_data["telemetry_snapshot"] = telemetry_snapshot
            elif "severity" in anomaly_data:
                severity = anomaly_data["severity"]
        else:
            if not source and (details is None or not details) and not severity:
                raise ValueError("Source and details cannot be empty")
            if details is None:
                details = {}
            anomaly_data = {
                "id": str(uuid.uuid4()),
                "source": source,
                "severity": severity,
                "details": details
            }
            if telemetry_snapshot is not None:
                anomaly_data["telemetry_snapshot"] = telemetry_snapshot

        try:
            telemetry = SystemTelemetry(repo_path=".")
            if hasattr(telemetry, "send"):
                telemetry.send(anomaly_data)
            elif hasattr(telemetry, "emit"):
                telemetry.emit(anomaly_data)
        except SystemTelemetryError:
            pass

        target_path = self._get_target_path()
        if target_path:
            parent_dir = os.path.dirname(os.path.abspath(target_path))
            os.makedirs(parent_dir, exist_ok=True)
            with open(target_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(anomaly_data) + '\n')

    def get_structured_report(self):
        target_path = self._get_target_path()
        if not target_path or not os.path.exists(target_path) or os.path.isdir(target_path):
            return []
        
        report = []
        with open(target_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        report.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return report

    def get_anomalies(self):
        return self.get_structured_report()

    def clear_logs(self):
        target_path = self._get_target_path()
        if target_path and os.path.exists(target_path) and not os.path.isdir(target_path):
            os.remove(target_path)