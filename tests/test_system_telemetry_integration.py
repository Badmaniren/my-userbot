import os
import unittest
from skills.system_telemetry import SystemTelemetry, ErrorPipeline, ErrorAnalyzer, AutoCorrector, start_new

class TestSystemTelemetryIntegration(unittest.TestCase):
    def setUp(self):
        self.telemetry = SystemTelemetry()
        self.pipeline = ErrorPipeline()
        self.analyzer = ErrorAnalyzer()
        self.corrector = AutoCorrector()
        self.test_log_path = "test_telemetry_error.log"

    def tearDown(self):
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)

    def test_end_to_end_pipeline_integration(self):
        start_result = start_new()
        self.assertTrue(start_result)

        pipeline_run = self.pipeline.run_pipeline(self.test_log_path)
        self.assertTrue(pipeline_run)
        self.assertTrue(os.path.exists(self.test_log_path))

        parse_result = self.analyzer.parse_log(self.test_log_path)
        self.assertTrue(parse_result)

        analyze_result = self.analyzer.analyze_and_prevent("CRITICAL_TEST_ERROR")
        self.assertTrue(analyze_result)

        correction_result = self.corrector.correct_code("CRITICAL_TEST_ERROR")
        self.assertTrue(correction_result)

if __name__ == "__main__":
    unittest.main()