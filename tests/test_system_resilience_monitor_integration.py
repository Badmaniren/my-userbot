import unittest
from skills.system_resilience_monitor import SystemResilienceMonitor
from skills.predictive_diagnostic_hub import PredictiveDiagnosticHub
from skills.error_pipeline import ErrorPipeline
from skills.telemetry_error_bridge import TelemetryErrorBridge


class TestSystemResilienceMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.monitor = SystemResilienceMonitor()
        self.predictive_hub = PredictiveDiagnosticHub()
        self.error_pipeline = ErrorPipeline()
        self.telemetry_bridge = TelemetryErrorBridge()

    def test_resilience_monitor_pipeline_integration(self):
        log_path = "test_system_log.log"
        stream_data = "CRITICAL_ERROR: telemetry sync failure"
        health_url = "http://localhost:8080/health"

        bridge_result = self.telemetry_bridge.process_telemetry_and_errors(stream_data)
        self.assertIsInstance(bridge_result, bool)

        pipeline_result = self.error_pipeline.run_pipeline(log_path)
        self.assertIsInstance(pipeline_result, bool)

        hub_result = self.predictive_hub.run_comprehensive_hub_pipeline(log_path, "ERR_SIG_001")
        self.assertIsInstance(hub_result, bool)

        verification_result = self.predictive_hub.verify_and_heal_system(health_url)
        self.assertIsInstance(verification_result, bool)


if __name__ == "__main__":
    unittest.main()