import json
import os
import subprocess

# Исключения
class AnomalyCorrelatorError(Exception): pass
class AnomalyDetectorError(Exception): pass
class AnomalyForecasterError(Exception): pass
class AnomalyPipelineError(Exception): pass
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


def start_new(payload):
    return {"status": "started", "payload": payload}


class AnomalyLogger:
    def __init__(self, log_path=None):
        self.log_path = log_path or "/tmp/anomaly_reactor.log"
        self._ensure_storage()

    def _ensure_storage(self):
        if self.log_path and not os.path.exists(self.log_path):
            dir_name = os.path.dirname(self.log_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def log_anomaly(self, source, severity, details, telemetry_snapshot):
        anomalies = self.get_anomalies()
        record = {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry_snapshot": telemetry_snapshot
        }
        anomalies.append(record)
        if self.log_path:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump(anomalies, f)

    def get_anomalies(self):
        if not self.log_path or not os.path.exists(self.log_path):
            return []
        try:
            with open(self.log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []

    def get_structured_report(self):
        return self.get_anomalies()

    def clear_logs(self):
        if self.log_path:
            with open(self.log_path, "w", encoding="utf-8") as f:
                json.dump([], f)


class GitInspector:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path or "."

    def _run_git(self, args):
        cmd = ["git"] + args
        try:
            result = subprocess.check_output(cmd, cwd=self.repo_path if os.path.exists(self.repo_path) else None)
            return result
        except Exception:
            return b""

    def get_file_diff(self, commit_hash):
        res = self._run_git(["show", commit_hash])
        return res.decode("utf-8", errors="ignore")

    def get_commit_history(self, max_count=10):
        res = self._run_git(["log", f"-n{max_count}", "--oneline"])
        return res.decode("utf-8", errors="ignore")

    def analyze_repository(self):
        res = self._run_git(["branch", "--show-current"])
        return res.decode("utf-8", errors="ignore").strip()

    def read_file_at_commit(self, commit_hash, file_path):
        res = self._run_git(["show", f"{commit_hash}:{file_path}"])
        return res.decode("utf-8", errors="ignore")

    def get_history(self):
        return self.get_commit_history()

    def get_latest_changes(self):
        return self.get_file_diff("HEAD")


class AutonomousReactorEngine:
    def handle_anomaly(self, anomaly):
        return {"status": "handled", "anomaly": anomaly}

anomaly_reactor = AutonomousReactorEngine()