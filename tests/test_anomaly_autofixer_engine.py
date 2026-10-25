import unittest
import os
import uuid
import random
import json
import tempfile
from unittest.mock import patch

from skills.anomaly_autofixer_engine import (
    AnomalyLogger,
    AnomalyAuditHub,
    ExtractorTool,
    GitInspector,
    start_new,
    AnomalyAlertDispatcherError,
    AnomalyCorrelatorError,
    AnomalyDetectorError,
    AnomalyForecasterError,
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
)


class TestAnomalyAutofixerEngine(unittest.TestCase):

    def setUp(self):
        self.rand_log_name = f"log_{uuid.uuid4().hex}.json"
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.temp_dir, self.rand_log_name)
        self.repo_path = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.log_path):
            try:
                os.remove(self.log_path)
            except OSError:
                pass
        if os.path.exists(self.temp_dir):
            try:
                os.rmdir(self.temp_dir)
            except OSError:
                pass

    def test_anomaly_logger_lifecycle(self):
        logger = AnomalyLogger(log_path=self.log_path)
        source = f"src_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry = {uuid.uuid4().hex: random.randint(1, 100)}

        logger.log_anomaly(source=source, severity=severity, details=details, telemetry_snapshot=telemetry)
        anomalies = logger.get_anomalies()
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["source"], source)
        self.assertEqual(anomalies[0]["severity"], severity)
        self.assertEqual(anomalies[0]["details"], details)
        self.assertEqual(anomalies[0]["telemetry_snapshot"], telemetry)

        report = logger.get_structured_report()
        self.assertEqual(report["total_anomalies"], 1)
        self.assertIn("anomalies", report)

        logger.clear_logs()
        self.assertEqual(len(logger.get_anomalies()), 0)

    def test_anomaly_audit_hub(self):
        threshold = random.uniform(10.0, 50.0)
        hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=threshold)

        source = f"source_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["INFO", "WARNING", "ERROR"])
        details = f"msg_{uuid.uuid4().hex}"
        telemetry = {uuid.uuid4().hex: random.random() if hasattr(random, 'random') else 0.5}

        hub.log_anomaly(source=source, severity=severity, details=details, telemetry_snapshot=telemetry)

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        below_val = threshold - random.uniform(1.0, 5.0)
        res_normal = hub.aggregate_and_report(metric_name=metric_name, value=below_val)
        self.assertEqual(res_normal["status"], "NORMAL")
        self.assertEqual(res_normal["metric_name"], metric_name)

        above_val = threshold + random.uniform(1.0, 5.0)
        res_exceed = hub.aggregate_and_report(metric_name=metric_name, value=above_val)
        self.assertEqual(res_exceed["status"], "EXCEEDS_THRESHOLD")

        final_report = hub.generate_final_report()
        self.assertEqual(final_report["repo_path"], self.repo_path)
        self.assertEqual(final_report["threshold"], threshold)
        self.assertEqual(len(final_report["metrics"]), 2)
        self.assertEqual(final_report["logs"]["total_anomalies"], 1)

    def test_extractor_tool(self):
        extractor = ExtractorTool()
        tag_name = f"tag_{uuid.uuid4().hex[:5]}"
        attr_key = f"key_{uuid.uuid4().hex[:5]}"
        attr_val = f"val_{uuid.uuid4().hex[:5]}"
        markup = f"<{tag_name} {attr_key}='{attr_val}' other=\"test\"></{tag_name}>"

        extracted = extractor.extract(markup)
        self.assertIn(tag_name, extracted)
        self.assertEqual(extracted[tag_name].get(attr_key), attr_val)
        self.assertEqual(extracted[tag_name].get("other"), "test")

        parsed_attrs = extractor.parse_attributes(f"{attr_key}=\"{attr_val}\" foo='bar'")
        self.assertEqual(parsed_attrs.get(attr_key), attr_val)
        self.assertEqual(parsed_attrs.get("foo"), "bar")

    def test_git_inspector_mocked(self):
        inspector = GitInspector(repo_path=self.repo_path)
        commit_hash = uuid.uuid4().hex
        file_path = f"src/{uuid.uuid4().hex[:6]}.py"
        fake_log_output = f"{commit_hash[:7]} fix bug {uuid.uuid4().hex[:4]}\n" + f"{uuid.uuid4().hex[:7]} initial commit"
        fake_show_output = f"diff --git a/{file_path} b/{file_path}\n+print('{uuid.uuid4().hex}')"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = fake_log_output
            history = inspector.get_commit_history(max_count=2)
            self.assertEqual(len(history), 2)
            self.assertIn(commit_hash[:7], history[0])

            mock_run.return_value.stdout = fake_show_output
            diff = inspector.get_file_diff(commit_hash)
            self.assertIn("diff --git", diff)

            analysis = inspector.analyze_repository()
            self.assertEqual(analysis["repo_path"], self.repo_path)
            self.assertIsInstance(analysis["recent_commits"], list)

            file_content = inspector.read_file_at_commit(commit_hash, file_path)
            self.assertIsInstance(file_content, str)

            latest_changes = inspector.get_latest_changes()
            self.assertIsInstance(latest_changes, str)

    def test_start_new_function(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex, "rand_id": random.randint(100, 999)}
        res = start_new(payload)
        self.assertEqual(res["status"], "started")
        self.assertEqual(res["payload"], payload)

    def test_all_exceptions_exist(self):
        exceptions = [
            AnomalyAlertDispatcherError,
            AnomalyCorrelatorError,
            AnomalyDetectorError,
            AnomalyForecasterError,
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
        for exc in exceptions:
            with self.subTest(exc=exc):
                instance = exc("test exception message")
                self.assertIsInstance(instance, Exception)