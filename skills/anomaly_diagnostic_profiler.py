import os
import re
import json
import sys
from types import ModuleType

class AnomalyLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path
        if os.path.isdir(self.log_path):
            self.file_path = os.path.join(self.log_path, "anomalies.log")
        else:
            self.file_path = self.log_path

        dir_name = os.path.dirname(self.file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write("")

    def log_anomaly(self, source: str, severity: str, details, telemetry_snapshot):
        record = {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry": telemetry_snapshot
        }
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def get_anomalies(self) -> list:
        if not os.path.exists(self.file_path):
            return []
        anomalies = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        anomalies.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return anomalies

    def get_structured_report(self) -> dict:
        anomalies = self.get_anomalies()
        report = {
            "total_count": len(anomalies),
            "anomalies": anomalies
        }
        return report

    def clear_logs(self) -> bool:
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("")
        return True


class AnomalyAuditHub:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        self.logger = AnomalyLogger(log_path)
        self.metrics = {}

    def log_anomaly(self, source: str, severity: str, details, telemetry_snapshot):
        self.logger.log_anomaly(source, severity, details, telemetry_snapshot)

    def aggregate_and_report(self, metric_name: str, value: float):
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)

    def generate_final_report(self) -> dict:
        return {
            "repo_path": self.repo_path,
            "threshold": self.threshold,
            "metrics": self.metrics,
            "logs_summary": self.logger.get_structured_report()
        }


class ExtractorTool:
    def extract(self, markup: str) -> dict:
        parsed = {}
        match = re.search(r'<(\w+)([^>]*)>', markup)
        if match:
            attrs_str = match.group(2)
            parsed = self.parse_attributes(attrs_str)
        return parsed

    def parse_attributes(self, attr_string: str) -> dict:
        attrs = {}
        pattern = r'(\w+)=(["\'])(.*?)\2'
        matches = re.findall(pattern, attr_string)
        for key, _, val in matches:
            attrs[key] = val
        return attrs


class GitInspector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def get_commit_history(self, max_count: int) -> list:
        return []

    def get_file_diff(self, commit_hash: str) -> str:
        return ""

    def read_file_at_commit(self, commit_hash: str, file_path: str) -> str:
        return ""

    def analyze_repository(self) -> dict:
        return {}


class SubModuleProxy(ModuleType):
    def __init__(self, name, mapping):
        super().__init__(name)
        self._mapping = mapping
    def __getattr__(self, attr):
        if attr in self._mapping:
            return self._mapping[attr]
        raise AttributeError(f"module '{self.__name__}' has no attribute '{attr}'")

sys.modules[__name__ + ".anomaly_audit_hub"] = SubModuleProxy("anomaly_audit_hub", {"AnomalyAuditHub": AnomalyAuditHub})
sys.modules[__name__ + ".anomaly_logger"] = SubModuleProxy("anomaly_logger", {"AnomalyLogger": AnomalyLogger})