import unittest
from skills.telemetry_error_bridge import TelemetryErrorBridge

class TestTelemetryErrorBridgeIntegration(unittest.TestCase):
    def setUp(self):
        self.bridge = TelemetryErrorBridge()

    def test_bridge_composition_and_analysis(self):
        stream_data = "CPU usage critical: 99% Error 500 Internal Server Error"

        telemetry_result = self.bridge.process_stream_data(stream_data)
        self.assertIsInstance(telemetry_result, bool)

        analysis_result = self.bridge.analyze_errors(stream_data)
        self.assertIsInstance(analysis_result, str)

        has_critical = self.bridge.has_critical_errors(stream_data)
        self.assertIsInstance(has_critical, bool)

if __name__ == '__main__':
    unittest.main()