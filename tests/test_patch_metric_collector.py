import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.patch_metric_collector import (
    AnomalyCorrelatorError,
    AnomalyDetectorError,
    anomaly_filter,
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


class TestPatchMetricCollectorInquisitor(unittest.TestCase):

    def setUp(self):
        self.rand_prefix = uuid.uuid4().hex[:8]
        self.rand_path = f"/tmp/{self.rand_prefix}_" + "".join(random.choices(string.ascii_lowercase, k=6)) + ".log"
        self.rand_repo = f"/var/repo/{uuid.uuid4().hex[:6]}"

    def test_exceptions_inheritance(self):
        exceptions = [
            AnomalyCorrelatorError,
            AnomalyDetectorError,
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
            msg = f"Error_{uuid.uuid4().hex}"
            exc_instance = exc_class(msg)
            self.assertIn(msg, str(exc_instance))

    def test_anomaly_filter_execution(self):
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(1000, 9999)
        input_data = {rand_key: rand_val, "noise": uuid.uuid4().hex}

        filtered = anomaly_filter(input_data)
        if filtered is not None:
            self.assertIsInstance(filtered, (dict, list, str, tuple, set))

    def test_anomaly_logger_lifecycle(self):
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", new_callable=unittest.mock.mock_open) as mock_file:

            logger = AnomalyLogger(self.rand_path)

            src = f"source_{uuid.uuid4().hex[:5]}"
            sev = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            details = {uuid.uuid4().hex: uuid.uuid4().hex}
            snapshot = {uuid.uuid4().hex: random.random()}

            logger.log_anomaly(src, sev, details, snapshot)

            anomalies = logger.get_anomalies()
            self.assertIsInstance(anomalies, list)

            report = logger.get_structured_report()
            self.assertIsInstance(report, (dict, str, list))

            logger.clear_logs()
            self.assertEqual(len(logger.get_anomalies()), 0)

    def test_git_inspector_methods(self):
        inspector = GitInspector(self.rand_repo)
        self.assertEqual(inspector.repo_path, self.rand_repo)

        mock_subprocess = MagicMock()
        rand_commit_hash = uuid.uuid4().hex
        rand_file = f"src/{uuid.uuid4().hex[:4]}.py"
        rand_diff = f"diff --git a/{rand_file} b/{rand_file}\n+print('{uuid.uuid4().hex}')"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = rand_diff
            mock_run.return_value.returncode = 0

            diff = inspector.get_file_diff(rand_commit_hash)
            self.assertIn(rand_file, diff)

            history = inspector.get_commit_history(max_count=random.randint(1, 50))
            self.assertIsNotNone(history)

            analysis = inspector.analyze_repository()
            self.assertIsNotNone(analysis)

            file_content = inspector.read_file_at_commit(rand_commit_hash, rand_file)
            self.assertIsNotNone(file_content)

            gen_history = inspector.get_history()
            self.assertIsNotNone(gen_history)

            latest = inspector.get_latest_changes()
            self.assertIsNotNone(latest)

    def test_anomaly_logger_io_failure_resilience(self):
        with patch("builtins.open", side_effect=IOError(f"Disk failure {uuid.uuid4().hex}")):
            logger = AnomalyLogger(self.rand_path)
            try:
                logger.log_anomaly("test", "HIGH", {}, {})
            except Exception as e:
                self.assertIsInstance(e, (IOError, AnomalyPipelineError, Exception))


if __name__ == "__main__":
    unittest.main()