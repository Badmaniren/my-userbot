import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import os

from skills.anomaly_reactor import (
    AnomalyCorrelatorError,
    AnomalyDetectorError,
    start_new,
    AnomalyForecasterError,
    AnomalyLogger,
    AnomalyPipelineError,
    AnomalyReportAggregatorError,
    AnomalyVisualizerError,
    AutonomousEngineError,
    CodeSanitizerError,
    CodeValidatorError,
    DigestDashboardBuilderError,
    DigestExporterError,
    GitInspector,
    HypothesisGeneratorError,
    LessonParserError,
    PatchAnalyzerError,
    PatchAutocorrectorError,
    PatchCheckerError,
    PatchEvaluatorError,
    PatchReporterError,
    StabilityDigestError,
    SystemTelemetryError
)


class TestAnomalyReactorInquisitor(unittest.TestCase):

    def setUp(self):
        self.rand_prefix = uuid.uuid4().hex[:8]
        self.rand_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.rand_source = f"source_{uuid.uuid4().hex[:6]}"
        self.rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.rand_details = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        self.rand_snapshot = {uuid.uuid4().hex: random.randint(1, 1000) for _ in range(2)}

    def test_exceptions_inheritance(self):
        exceptions = [
            AnomalyCorrelatorError,
            AnomalyDetectorError,
            AnomalyForecasterError,
            AnomalyPipelineError,
            AnomalyReportAggregatorError,
            AnomalyVisualizerError,
            AutonomousEngineError,
            CodeSanitizerError,
            CodeValidatorError,
            DigestDashboardBuilderError,
            DigestExporterError,
            HypothesisGeneratorError,
            LessonParserError,
            PatchAnalyzerError,
            PatchAutocorrectorError,
            PatchCheckerError,
            PatchEvaluatorError,
            PatchReporterError,
            StabilityDigestError,
            SystemTelemetryError
        ]
        for exc_class in exceptions:
            exc_msg = uuid.uuid4().hex
            exc_instance = exc_class(exc_msg)
            self.assertIsInstance(exc_instance, Exception)
            self.assertEqual(str(exc_instance), exc_msg)

    def test_anomaly_filter_start_new(self):
        payload_data = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "metric": random.uniform(10.0, 99.9)
        }
        res = start_new(payload_data)
        self.assertIsNotNone(res)

    def test_anomaly_logger_lifecycle(self):
        logger = AnomalyLogger(log_path=self.rand_path)
        
        logger.log_anomaly(
            source=self.rand_source,
            severity=self.rand_severity,
            details=self.rand_details,
            telemetry_snapshot=self.rand_snapshot
        )
        
        anomalies = logger.get_anomalies()
        self.assertGreaterEqual(len(anomalies), 1)
        
        found = False
        for anom in anomalies:
            if anom.get("source") == self.rand_source:
                found = True
                self.assertEqual(anom.get("severity"), self.rand_severity)
                self.assertEqual(anom.get("details"), self.rand_details)
                self.assertEqual(anom.get("telemetry_snapshot"), self.rand_snapshot)
        self.assertTrue(found)

        report = logger.get_structured_report()
        self.assertIsInstance(report, (dict, str, list))

        logger.clear_logs()
        cleared_anomalies = logger.get_anomalies()
        self.assertEqual(len(cleared_anomalies), 0)

    def test_git_inspector_methods(self):
        repo_dir = f"/tmp/repo_{uuid.uuid4().hex}"
        inspector = GitInspector(repo_path=repo_dir)
        
        target_commit = uuid.uuid4().hex
        target_file = f"{uuid.uuid4().hex}.py"
        target_diff = f"diff --git a/{target_file} b/{target_file}\n+{uuid.uuid4().hex}"
        target_file_content = f"# {uuid.uuid4().hex}\nprint('{uuid.uuid4().hex}')"

        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = target_diff.encode('utf-8')
            
            diff_res = inspector.get_file_diff(commit_hash=target_commit)
            self.assertIn(target_file, diff_res) or self.assertIsInstance(diff_res, str)

        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = f"{target_commit} - msg".encode('utf-8')
            history = inspector.get_commit_history(max_count=random.randint(1, 50))
            self.assertIsInstance(history, (list, str))

        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = f"branch_{uuid.uuid4().hex}".encode('utf-8')
            analysis = inspector.analyze_repository()
            self.assertIsNotNone(analysis)

        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = target_file_content.encode('utf-8')
            file_content = inspector.read_file_at_commit(commit_hash=target_commit, file_path=target_file)
            self.assertIsInstance(file_content, str)

        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = target_commit.encode('utf-8')
            hist = inspector.get_history()
            self.assertIsNotNone(hist)

        with patch("subprocess.check_output") as mock_subprocess:
            mock_subprocess.return_value = target_file_content.encode('utf-8')
            latest = inspector.get_latest_changes()
            self.assertIsNotNone(latest)