import unittest
from skills.autonomous_recovery_agent import *
from skills.predictive_diagnostic_hub import PredictiveDiagnosticHub
from skills.diagnostic_action_hub import DiagnosticActionHub
from skills.error_analyzer import ErrorAnalyzer
from skills.error_pipeline import ErrorPipeline
from skills.diagnostic_reporter import DiagnosticReporter
from skills.auto_corrector import AutoCorrector

class TestAutonomousRecoveryAgentIntegration(unittest.TestCase):
    def test_recovery_agent_full_integration(self):
        pred_hub = PredictiveDiagnosticHub()
        action_hub = DiagnosticActionHub()
        analyzer = ErrorAnalyzer()
        pipeline = ErrorPipeline()
        reporter = DiagnosticReporter()
        corrector = AutoCorrector()

        test_log_path = "test_system_error.log"
        test_signature = "CRITICAL_SERVICE_FAILURE"
        test_stream = {"stream": "data_anomaly"}
        test_url = "http://localhost:8080/health"

        parse_res = analyzer.parse_log(test_log_path)
        self.assertIsInstance(parse_res, bool)

        stream_res = analyzer.process_stream(test_stream)
        self.assertIsInstance(stream_res, bool)

        pipeline_res = pipeline.run_pipeline(test_log_path)
        self.assertIsInstance(pipeline_res, bool)

        report_res = reporter.generate_report(test_log_path, test_stream)
        self.assertIsInstance(report_res, bool)

        health_res = reporter.verify_system_health(test_url)
        self.assertIsInstance(health_res, bool)

        correct_res = corrector.correct_code(test_signature)
        self.assertIsInstance(correct_res, bool)

        hub_res = action_hub.handle_critical_failure(test_log_path, test_signature)
        self.assertIsInstance(hub_res, bool)

        autonomous_res = pred_hub.run_autonomous_center(test_log_path, test_signature)
        self.assertIsInstance(autonomous_res, bool)

        heal_res = pred_hub.verify_and_heal_system(test_url)
        self.assertIsInstance(heal_res, bool)

if __name__ == "__main__":
    unittest.main()