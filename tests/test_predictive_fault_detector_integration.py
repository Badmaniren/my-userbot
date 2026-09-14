import unittest
from skills.predictive_fault_detector import PredictiveFaultDetector
from skills.telemetry_error_bridge import TelemetryErrorBridge
from skills.error_analyzer import ErrorAnalyzer
from skills.diagnostic_action_hub import DiagnosticActionHub

class TestPredictiveFaultDetectorIntegration(unittest.TestCase):
    def setUp(self):
        self.detector = PredictiveFaultDetector()
        self.bridge = TelemetryErrorBridge()
        self.analyzer = ErrorAnalyzer()
        self.hub = DiagnosticActionHub()

    def test_predictive_fault_detector_integration(self):
        stream_data = "WARNING: Memory usage spikes predicted in telemetry stream"
        
        bridge_result = self.bridge.process_telemetry_and_errors(stream_data)
        self.assertIsInstance(bridge_result, bool)

        analyzer_result = self.analyzer.process_stream(stream_data)
        self.assertIsInstance(analyzer_result, bool)

        hub_result = self.hub.process_stream_action(stream_data)
        self.assertIsInstance(hub_result, bool)

if __name__ == '__main__':
    unittest.main()