import os
import json
import xml.etree.ElementTree as ET

# --- Исключения ---

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


# --- Модули логирования и аудита ---

class AnomalyLogger:
    def __init__(self, log_path: str):
        self.log_path = log_path
        log_dir = os.path.dirname(self.log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def log_anomaly(self, source: str, severity: str, details: str, telemetry_snapshot: dict):
        anomalies = self.get_anomalies()
        record = {
            "source": source,
            "severity": severity,
            "details": details,
            "telemetry": telemetry_snapshot
        }
        anomalies.append(record)
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(anomalies, f, ensure_ascii=False, indent=2)

    def get_structured_report(self) -> dict:
        return {"anomalies_count": len(self.get_anomalies()), "logs": self.get_anomalies()}

    def get_anomalies(self) -> list:
        if not os.path.exists(self.log_path):
            return []
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                try:
                    data = json.loads(content)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return [data]
                except json.JSONDecodeError:
                    pass

                anomalies = []
                for line in content.splitlines():
                    line = line.strip()
                    if line:
                        try:
                            item = json.loads(line)
                            anomalies.append(item)
                        except json.JSONDecodeError:
                            pass
                return anomalies
        except OSError as e:
            raise AnomalyReportAggregatorError(f"Failed to read anomalies log: {e}") from e

    def clear_logs(self):
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump([], f)


class AnomalyAuditHub:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        self.logger = AnomalyLogger(log_path)
        self.metrics = {}

    def log_anomaly(self, source: str, severity: str, details: str, telemetry_snapshot: dict):
        self.logger.log_anomaly(source, severity, details, telemetry_snapshot)

    def aggregate_and_report(self, metric_name: str, value: float) -> dict:
        self.metrics[metric_name] = value
        return {metric_name: value}

    def generate_final_report(self) -> str:
        report = {
            "repo_path": self.repo_path,
            "threshold": self.threshold,
            "metrics": self.metrics,
            "anomalies": self.logger.get_anomalies()
        }
        return json.dumps(report)


# --- Инструменты извлечения и инспекции ---

class ExtractorTool:
    def extract(self, markup_data: str) -> dict:
        result = {}
        try:
            root = ET.fromstring(markup_data)
            result[root.tag] = root.text
        except ET.ParseError as e:
            raise CodeSanitizerError(f"Failed to parse markup data: {e}") from e
        return result

    def parse_attributes(self, tag_string_input: str) -> dict:
        parsed = {}
        parts = tag_string_input.split('=')
        if len(parts) == 2:
            key = parts[0].strip()
            val = parts[1].strip().strip('"\'')
            parsed[key] = val
        return parsed


class GitInspector:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def get_commit_history(self, max_commits: int) -> list:
        return ["dummy_commit_hash"] * min(max_commits, 1)

    def get_file_diff(self, commit_hash: str) -> str:
        return f"diff_for_{commit_hash}"

    def analyze_repository(self) -> dict:
        return {"status": "analyzed", "repo": self.repo_path}

    def read_file_at_commit(self, commit_hash: str, file_path: str) -> str:
        return f"content_of_{file_path}_at_{commit_hash}"

    def get_history(self) -> list:
        return ["dummy_history_commit"]

    def get_latest_changes(self) -> str:
        return "latest_changes_dummy"


# --- Вспомогательные функции конвейера ---

def start_new(raw_data: dict) -> dict:
    if not isinstance(raw_data, dict):
        return {}
    return {k: v for k, v in raw_data.items() if v is not None}


class AnomalyPipeline:
    def __init__(self, repo_path: str = ".", log_path: str = "/tmp/anomaly_audit.log", threshold: float = 0.5):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        self.hub = AnomalyAuditHub(repo_path, log_path, threshold)
        self.logger = AnomalyLogger(log_path)

    def process_anomaly(self, source: str, severity: str, details: str, telemetry_snapshot: dict):
        return self.hub.log_anomaly(source, severity, details, telemetry_snapshot)

    def process_and_log_anomaly(self, source: str, severity: str, details: str, telemetry_snapshot: dict):
        return self.hub.log_anomaly(source, severity, details, telemetry_snapshot)

    def aggregate_pipeline_metric(self, metric_name: str, value: float) -> dict:
        return self.hub.aggregate_and_report(metric_name, value)

    def generate_final_report(self) -> str:
        return self.hub.generate_final_report()

    def get_pipeline_structured_report(self) -> dict:
        return self.logger.get_structured_report()


def anomaly_pipeline_main(repo_path: str, log_path: str, threshold: float) -> dict:
    hub = AnomalyAuditHub(repo_path, log_path, threshold)
    inspector = GitInspector(repo_path)
    history = inspector.get_history()

    hub.aggregate_and_report("pipeline_runs", 1.0)
    report = hub.generate_final_report()

    return {
        "status": "success",
        "history_count": len(history),
        "report": report
    }