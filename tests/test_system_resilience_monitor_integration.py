import unittest
import os
from skills.system_resilience_monitor import (
    SystemResilienceMonitor,
    PredictiveDiagnosticHub,
    ErrorPipeline,
    TelemetryErrorBridge
)

class TestSystemResilienceMonitorIntegration(unittest.TestCase):
    def setUp(self):
        self.monitor = SystemResilienceMonitor()
        self.predictive_hub = PredictiveDiagnosticHub()
        self.error_pipeline = ErrorPipeline()
        self.telemetry_bridge = TelemetryErrorBridge()
        self.test_log_path = "test_system_resilience.log"

    def tearDown(self):
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)

    def test_comprehensive_resilience_pipeline(self):
        hub_result = self.predictive_hub.run_comprehensive_hub_pipeline(self.test_log_path, "TEST_SIG")
        self.assertTrue(hub_result)
        self.assertTrue(os.path.exists(self.test_log_path))

        heal_result = self.predictive_hub.verify_and_heal_system("http://localhost")
        self.assertTrue(heal_result)

        pipeline_result = self.error_pipeline.run_pipeline(self.test_log_path)
        self.assertTrue(pipeline_result)

        analyzer_result = self.error_pipeline.analyzer.parse_log(self.test_log_path)
        self.assertTrue(analyzer_result)

        telemetry_result = self.telemetry_bridge.process_telemetry_and_errors("TEST_STREAM_DATA")
        self.assertTrue(telemetry_result)

if __name__ == "__main__":
    unittest.main()