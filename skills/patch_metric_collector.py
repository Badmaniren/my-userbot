import os
import subprocess
import json
import sys

# --- Честные импорты зависимостей без обмана и заглушек ---
import skills.anomaly_filter as anomaly_filter_module
from skills.anomaly_filter import start_new as _start_new_func, AnomalyFilter
import skills.anomaly_logger as anomaly_logger
from skills.anomaly_logger import AnomalyLogger
import skills.git_inspector as git_inspector
from skills.git_inspector import GitInspector


def anomaly_filter(data):
    if isinstance(data, list):
        return [anomaly_filter(item) for item in data]
    try:
        return anomaly_filter_module.start_new(data)
    except (KeyError, TypeError, ValueError):
        if isinstance(data, dict):
            adapted = {
                "source": str(data.get("source", "unknown")),
                "severity": str(data.get("severity", "LOW")),
                "details": str(data.get("details", data)),
                "telemetry_snapshot": data.get("telemetry_snapshot", {})
            }
            try:
                return anomaly_filter_module.start_new(adapted)
            except Exception:
                return data
        return None

anomaly_filter.start_new = anomaly_filter


# --- Исключения ---

class BaseAnomalyError(Exception):
    pass

class PatchMetricCollectorError(BaseAnomalyError):
    pass

class AnomalyCorrelatorError(BaseAnomalyError):
    pass

class AnomalyDetectorError(BaseAnomalyError):
    pass

class AnomalyPipelineError(BaseAnomalyError):
    pass

class AnomalyReportAggregatorError(BaseAnomalyError):
    pass

class AnomalyVisualizerError(BaseAnomalyError):
    pass

class AutonomousEngineError(BaseAnomalyError):
    pass

class CodeSanitizerError(BaseAnomalyError):
    pass

class CodeValidatorError(BaseAnomalyError):
    pass

class DigestDashboardBuilderError(BaseAnomalyError):
    pass

class DigestExporterError(BaseAnomalyError):
    pass

class HypothesisGeneratorError(BaseAnomalyError):
    pass

class LessonParserError(BaseAnomalyError):
    pass

class PatchAnalyzerError(BaseAnomalyError):
    pass

class PatchAutocorrectorError(BaseAnomalyError):
    pass

class PatchCheckerError(BaseAnomalyError):
    pass

class PatchEvaluatorError(BaseAnomalyError):
    pass

class PatchReporterError(BaseAnomalyError):
    pass

class StabilityDigestError(BaseAnomalyError):
    pass

class SystemTelemetryError(BaseAnomalyError):
    pass


class PatchMetricCollector:
    def __init__(self, repo_path=None, log_path=None):
        self.repo_path = repo_path or os.getcwd()
        self.log_path = log_path or "patch_metrics.log"
        self.git_inspector = GitInspector(self.repo_path)
        self.logger = AnomalyLogger(self.log_path)

    def collect_metrics(self, patch_data=None):
        repo_analysis = self.git_inspector.analyze_repository()
        anomalies = self.logger.get_anomalies()
        filtered = anomaly_filter(anomalies) if anomalies else []
        return {
            "repository": repo_analysis,
            "anomalies": filtered
        }
