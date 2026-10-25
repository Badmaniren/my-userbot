import os
import re
import json
import subprocess

# --- Exceptions ---

class AnomalyAlertDispatcherError(Exception): pass
class AnomalyCorrelatorError(Exception): pass
class AnomalyDetectorError(Exception): pass
class AnomalyForecasterError(Exception): pass
class AnomalyReportAggregatorError(Exception): pass
class AnomalyVisualizerError(Exception): pass
class AutonomousEngineError(Exception): pass
class CodeSanitizerError(Exception): pass
class CodeValidatorError(Exception): pass
class DigestDashboardBuilderError(Exception): pass
class DigestExporterError(Exception): pass
class HypothesisGeneratorError(Exception): pass
class LessonParserError(Exception): pass
class PatchAnalyzerError(Exception): pass
class PatchAutocorrectorError(Exception): pass
class PatchCheckerError(Exception): pass
class PatchEvaluatorError(Exception): pass
class PatchReporterError(Exception): pass
class StabilityDigestError(Exception): pass
class SystemTelemetryError(Exception): pass


# --- Classes and Functions ---

class AnomalyLogger:
    def __init__(self, log_path: str = None):
        self.log_path = log_path or "anomaly.log"
        self._ensure_log_file()

    def _ensure_log_file(self):
        directory = os.path.dirname(self.log_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def clear_logs(self):
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump([], f)

    def log_anomaly(self, source: str, severity: str, details, telemetry_snapshot: dict):
        record = {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry_snapshot": telemetry_snapshot
        }
        with open(self.log_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data.append(record)
        with open(self.log_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_anomalies(self) -> list:
        with open(self.log_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_structured_report(self) -> dict:
        anomalies = self.get_anomalies()
        report = {
            "total_anomalies": len(anomalies),
            "anomalies": anomalies
        }
        return report


class AnomalyAuditHub:
    def __init__(self, repo_path: str = None, log_path: str = None, threshold: float = 0.0):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        self.logger = AnomalyLogger(log_path=self.log_path)
        self.metrics = []

    def log_anomaly(self, source: str, severity: str, details, telemetry_snapshot: dict):
        self.logger.log_anomaly(source=source, severity=severity, details=details, telemetry_snapshot=telemetry_snapshot)

    def aggregate_and_report(self, metric_name: str, value: float) -> dict:
        self.metrics.append({"metric_name": metric_name, "value": value})
        res = {
            "metric_name": metric_name,
            "value": value,
            "status": "EXCEEDS_THRESHOLD" if value > self.threshold else "NORMAL"
        }
        return res

    def generate_final_report(self) -> dict:
        return {
            "repo_path": self.repo_path,
            "threshold": self.threshold,
            "metrics": self.metrics,
            "logs": self.logger.get_structured_report()
        }


class ExtractorTool:
    def extract(self, markup: str) -> dict:
        tags = re.findall(r'<([a-zA-Z0-9_-]+)([^>]*)>', markup)
        result = {}
        for tag, attr_string in tags:
            attrs = self.parse_attributes(attr_string)
            result[tag] = attrs
        return result

    def parse_attributes(self, tag_string: str) -> dict:
        pattern = r'([a-zA-Z0-9_-]+)=[\"\']([^\"\']*)[\"\']'
        matches = re.findall(pattern, tag_string)
        return {k: v for k, v in matches}


class GitInspector:
    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or "."

    def _run_git_command(self, args):
        cmd = ["git"] + args
        result = subprocess.run(
            cmd,
            cwd=self.repo_path if os.path.isdir(self.repo_path) else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip()

    def get_commit_history(self, max_count: int = 10) -> list:
        out = self._run_git_command(["log", f"-n", str(max_count), "--oneline"])
        if not out:
            return []
        return out.split("\n")

    def get_file_diff(self, commit_hash: str) -> str:
        return self._run_git_command(["show", commit_hash])

    def analyze_repository(self) -> dict:
        history = self.get_commit_history(max_count=5)
        return {
            "repo_path": self.repo_path,
            "recent_commits": history
        }

    def read_file_at_commit(self, commit_hash: str, file_path: str) -> str:
        return self._run_git_command(["show", f"{commit_hash}:{file_path}"])

    def get_history(self) -> list:
        return self.get_commit_history()

    def get_latest_changes(self) -> str:
        return self._run_git_command(["log", "-n", "1", "-p"])


def start_new(data_payload: dict) -> dict:
    return {
        "status": "started",
        "payload": data_payload
    }