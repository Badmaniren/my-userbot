import unittest
import tempfile
import os
from skills.diagnostic_action_hub import DiagnosticActionHub
from skills.ai_diagnostic_agent import AutoCorrector
from skills.diagnostic_reporter import DiagnosticReporter

class TestDiagnosticActionHubIntegration(unittest.TestCase):
    def setUp(self):
        self.hub = DiagnosticActionHub()
        self.corrector = AutoCorrector()
        self.reporter = DiagnosticReporter()
        
        self.test_fd, self.test_log_path = tempfile.mkstemp(suffix=".log")
        os.close(self.test_fd)
        
        with open(self.test_log_path, "w") as f:
            f.write("CRITICAL: Test critical error signature 500")

    def tearDown(self):
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)

    def test_composition_and_execution(self):
        self.assertIsInstance(self.hub, DiagnosticActionHub)
        
        report_result = self.reporter.generate_report(self.test_log_path, "stream_test")
        self.assertIsInstance(report_result, bool)

        correction_result = self.corrector.parse_and_correct_log_file(self.test_log_path)
        self.assertIsInstance(correction_result, bool)

        if hasattr(self.hub, "run_hub_pipeline"):
            hub_res = self.hub.run_hub_pipeline(self.test_log_path, "stream_test")
            self.assertIsInstance(hub_res, bool)
        elif hasattr(self.hub, "process_action_hub"):
            hub_res = self.hub.process_action_hub(self.test_log_path)
            self.assertIsInstance(hub_res, bool)

if __name__ == "__main__":
    unittest.main()