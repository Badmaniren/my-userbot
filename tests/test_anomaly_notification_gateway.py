import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.anomaly_notification_gateway import (
    AnomalyAuditHub,
    AnomalyLogger,
    AnomalyNotificationGateway,
    AnomalyNotificationGatewayError,
    route_and_format_notification,
    start_new,
    AnomalyAlertDispatcherError,
    AutofixerWorkerError,
    AnomalyCorrelatorError,
    AnomalyDetectorError,
    AnomalyForecasterError,
    AnomalyReportAggregatorError,
    AnomalyRollbackControllerError,
    AnomalyVisualizerError,
    AutonomousEngineError,
    CodeSanitizerError,
    CodeValidatorError,
    DigestDashboardBuilderError,
    DigestExporterError,
    ExtractorTool,
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

class TestAnomalyNotificationGateway(unittest.TestCase):

    def setUp(self):
        self.rand_str_1 = uuid.uuid4().hex
        self.rand_str_2 = uuid.uuid4().hex
        self.rand_float = random.uniform(1.0, 100.0)
        self.rand_int = random.randint(1, 1000)

    def test_exceptions_instantiation(self):
        exc_classes = [
            AnomalyNotificationGatewayError,
            AnomalyAlertDispatcherError,
            AutofixerWorkerError,
            AnomalyCorrelatorError,
            AnomalyDetectorError,
            AnomalyForecasterError,
            AnomalyReportAggregatorError,
            AnomalyRollbackControllerError,
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
        for exc_cls in exc_classes:
            exc_instance = exc_cls(self.rand_str_1)
            self.assertIsInstance(exc_instance, Exception)
            self.assertEqual(str(exc_instance), self.rand_str_1)

    def test_anomaly_notification_gateway_class(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        gateway = AnomalyNotificationGateway(repo_path, log_path, self.rand_float)

        self.assertEqual(gateway.repo_path, repo_path)
        self.assertEqual(gateway.log_path, log_path)
        self.assertEqual(gateway.threshold, self.rand_float)

        source = f"src_{uuid.uuid4().hex}"
        severity = "HIGH"
        details = {"error_code": 500}

        with patch('skills.anomaly_notification_gateway.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            res = gateway.process_and_route(source, severity, details)
            self.assertEqual(res["status"], "routed")
            self.assertIn("formatted_message", res)

    def test_route_and_format_notification_and_start_new(self):
        payload = {
            "source": "sys_test",
            "severity": "CRITICAL",
            "details": {"msg": "failure"}
        }
        res = route_and_format_notification(payload)
        self.assertEqual(res["status"], "routed")
        self.assertIn("CRITICAL", res["formatted_message"])

        raw = {"error_code": 404, "msg": "not found"}
        filtered = start_new(raw)
        self.assertTrue(filtered["filtered"])
        self.assertEqual(filtered["original_error"], 404)

        non_dict_filtered = start_new(None)
        self.assertTrue(non_dict_filtered["filtered"])

    def test_anomaly_audit_hub_and_logger(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        hub = AnomalyAuditHub(repo_path, log_path, self.rand_float)

        self.assertEqual(hub.repo_path, repo_path)
        self.assertEqual(hub.log_path, log_path)
        self.assertEqual(hub.threshold, self.rand_float)

        source = f"src_{uuid.uuid4().hex}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry = {uuid.uuid4().hex: random.random()}

        with patch('skills.anomaly_notification_gateway.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            hub.log_anomaly(source, severity, details, telemetry)
            mock_file.write.assert_called()

        metric_name = f"metric_{uuid.uuid4().hex}"
        agg_result = hub.aggregate_and_report(metric_name, self.rand_float)
        self.assertIsNotNone(agg_result)

        final_rep = hub.generate_final_report()
        self.assertIsInstance(final_rep, (dict, str, list))

    def test_anomaly_logger_methods(self):
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        logger = AnomalyLogger(log_path)

        source = f"src_{uuid.uuid4().hex}"
        severity = random.choice(["INFO", "WARNING", "ERROR"])
        details = f"msg_{uuid.uuid4().hex}"
        telemetry = [random.randint(0, 50) for _ in range(3)]

        with patch('skills.anomaly_notification_gateway.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            logger.log_anomaly(source, severity, details, telemetry)
            mock_file.write.assert_called()

        anomalies = logger.get_anomalies()
        self.assertIsInstance(anomalies, list)

        report = logger.get_structured_report()
        self.assertIsNotNone(report)

        logger.clear_logs()

    def test_extractor_tool_behavior(self):
        tool = ExtractorTool()
        tag = f"<{uuid.uuid4().hex} attr='{self.rand_str_1}'></{uuid.uuid4().hex}>"
        parsed = tool.parse_attributes(f"attr='{self.rand_str_1}'")
        self.assertIsInstance(parsed, dict)

        extracted = tool.extract(tag)
        self.assertIsInstance(extracted, dict)

    def test_git_inspector(self):
        repo_path = f"/var/repo/{uuid.uuid4().hex}"
        inspector = GitInspector(repo_path)
        self.assertEqual(inspector.repo_path, repo_path)

        commit_hash = uuid.uuid4().hex
        file_path = f"file_{uuid.uuid4().hex}.py"

        with patch('subprocess.check_output') as mock_sub:
            mock_sub.return_value = bytes(self.rand_str_1, 'utf-8')

            history = inspector.get_commit_history(self.rand_int)
            self.assertIsNotNone(history)

            diff = inspector.get_file_diff(commit_hash)
            self.assertIsNotNone(diff)

            repo_analysis = inspector.analyze_repository()
            self.assertIsNotNone(repo_analysis)

            file_content = inspector.read_file_at_commit(commit_hash, file_path)
            self.assertIsNotNone(file_content)

            latest = inspector.get_latest_changes()
            self.assertIsNotNone(latest)

if __name__ == '__main__':
    unittest.main()
