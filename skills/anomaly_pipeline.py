import os
import json
import re

class AnomalyLogger:
    def __init__(self, log_path=None):
        self.log_path = log_path or "anomaly.log"
        log_dir = os.path.dirname(self.log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def clear_logs(self):
        if os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write("")

    def log_anomaly(self, source, severity, details, telemetry):
        record = {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry": telemetry
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def get_anomalies(self):
        anomalies = []
        if not os.path.exists(self.log_path):
            return anomalies
        
        content = ""
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return anomalies

        if not content:
            return anomalies

        lines = content.splitlines()
        for line in lines:
            line = line.strip()
            if line:
                try:
                    anomalies.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return anomalies

    def get_structured_report(self):
        return {"anomalies": self.get_anomalies()}


class AnomalyAuditHub:
    def __init__(self, repo_path, log_path, threshold):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        self.logger = AnomalyLogger(log_path)
        self.metrics = []

    def log_anomaly(self, source, severity, details, telemetry_snapshot):
        self.logger.log_anomaly(source, severity, details, telemetry_snapshot)

    def aggregate_and_report(self, metric_name, metric_value):
        self.metrics.append({"name": metric_name, "value": metric_value})
        return True

    def generate_final_report(self):
        return {
            "report_id": "report_" + os.path.basename(self.log_path),
            "metrics": self.metrics,
            "anomalies": self.logger.get_anomalies()
        }


def start_new(input_data):
    if isinstance(input_data, dict):
        res = dict(input_data)
        res['filtered'] = True
        return res
    return {'filtered': True, 'data': input_data}


def start_pipeline(input_data=None):
    return start_new(input_data or {})


class ExtractorTool:
    def parse_attributes(self, tag_string):
        attrs = {}
        pattern = r'([a-zA-Z0-9_-]+)=["\']([^"\']*)["\']'
        matches = re.findall(pattern, tag_string)
        for key, val in matches:
            attrs[key] = val
        return attrs

    def extract(self, markup):
        return {"markup": markup, "parsed": True}


class GitInspector:
    def __init__(self, repo_path):
        self.repo_path = repo_path

    def get_commit_history(self, max_count=10):
        return [{"commit": "mock_commit_hash"}]

    def read_file_at_commit(self, commit_hash, filepath):
        return b"random_file_content"

    def analyze_repository(self):
        return {"status": "clean"}