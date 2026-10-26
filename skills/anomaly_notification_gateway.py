import json
import os
import subprocess
import datetime

# ==========================================
# ИСКЛЮЧЕНИЯ
# ==========================================

class AnomalyNotificationGatewayError(Exception): pass
class AnomalyAlertDispatcherError(Exception): pass
class AutofixerWorkerError(Exception): pass
class AnomalyCorrelatorError(Exception): pass
class AnomalyDetectorError(Exception): pass
class AnomalyForecasterError(Exception): pass
class AnomalyReportAggregatorError(Exception): pass
class AnomalyRollbackControllerError(Exception): pass
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


# ==========================================
# КОМПОНЕНТЫ И КЛАССЫ
# ==========================================

class AnomalyLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path

    def log_anomaly(self, source: str, severity: str, details, telemetry):
        record = {
            "timestamp": str(datetime.datetime.now()),
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry": telemetry
        }
        dir_name = os.path.dirname(os.path.abspath(self.log_path))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def get_anomalies(self) -> list:
        if not os.path.exists(self.log_path):
            return []
        anomalies = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    anomalies.append(json.loads(line))
        return anomalies

    def get_structured_report(self) -> dict:
        anomalies = self.get_anomalies()
        return {
            "total_count": len(anomalies),
            "anomalies": anomalies
        }

    def clear_logs(self):
        if os.path.exists(self.log_path):
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write("")


class AnomalyAuditHub:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        self.logger = AnomalyLogger(log_path)

    def log_anomaly(self, source: str, severity: str, details, telemetry_snapshot):
        self.logger.log_anomaly(source, severity, details, telemetry_snapshot)

    def aggregate_and_report(self, metric_name: str, value: float) -> dict:
        return {
            "metric_name": metric_name,
            "value": value,
            "threshold": self.threshold,
            "status": "ALERT" if value > self.threshold else "NORMAL"
        }

    def generate_final_report(self) -> dict:
        return {
            "repo": self.repo_path,
            "threshold": self.threshold,
            "summary": self.logger.get_structured_report()
        }


class ExtractorTool:
    def parse_attributes(self, attr_string: str) -> dict:
        return {"parsed": attr_string}

    def extract(self, tag_string: str) -> dict:
        return {"tag": tag_string}


class GitInspector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def _run_git(self, args: list) -> str:
        cmd = ["git", "-C", self.repo_path] + args
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return output.decode("utf-8")

    def get_commit_history(self, limit: int = 10) -> str:
        return self._run_git(["log", "-n", str(limit)])

    def get_file_diff(self, commit_hash: str) -> str:
        return self._run_git(["show", commit_hash])

    def analyze_repository(self) -> str:
        return self._run_git(["status"])

    def read_file_at_commit(self, commit_hash: str, file_path: str) -> str:
        return self._run_git(["show", f"{commit_hash}:{file_path}"])

    def get_latest_changes(self) -> str:
        return self._run_git(["diff", "HEAD~1", "HEAD"])


class AnomalyNotificationGateway:
    def __init__(self, repo_path: str = ".", log_path: str = "/tmp/anomaly_audit.log", threshold: float = 0.5):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        self.audit_hub = AnomalyAuditHub(repo_path, log_path, threshold)

    def route_and_format_notification(self, payload: dict) -> dict:
        return route_and_format_notification(payload)

    def process_and_route(self, source: str, severity: str, details: dict, telemetry: dict = None) -> dict:
        payload = {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry": telemetry or {}
        }
        self.audit_hub.log_anomaly(source, severity, details, telemetry or {})
        return route_and_format_notification(payload)


# ==========================================
# ДОПОЛНИТЕЛЬНЫЕ МОДУЛИ ДЛЯ ИНТЕГРАЦИИ
# ==========================================

def start_new(raw_details: dict) -> dict:
    if not isinstance(raw_details, dict):
        raw_details = {}
    return {
        "filtered": True,
        "original_error": raw_details.get("error_code"),
        **raw_details
    }


def route_and_format_notification(payload: dict) -> dict:
    source = payload.get("source", "unknown")
    severity = payload.get("severity", "INFO")
    msg = f"Notification Gateway [Source: {source}] [Severity: {severity}] processed successfully."
    return {
        "status": "routed",
        "formatted_message": msg,
        "payload_received": payload
    }
