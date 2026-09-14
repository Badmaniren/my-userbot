import unittest
from skills.telemetry_analyzer import TelemetryAnalyzer
from skills import system_telemetry
from skills import error_analyzer

class TestTelemetryAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.analyzer = TelemetryAnalyzer()

    def test_telemetry_and_error_composition(self):
        test_stream = {"cpu_usage": 85.5, "memory_usage": 90.0, "error_log": "CRITICAL: System overload"}

        telemetry_result = system_telemetry.process_stream_data(test_stream)

        has_critical = error_analyzer.has_critical_errors("CRITICAL: System overload")
        self.assertTrue(has_critical)

        combined_analysis = error_analyzer.analyze_errors("CRITICAL: System overload")
        self.assertIsInstance(combined_analysis, str)

        report_saved = error_analyzer.save_error_report(combined_analysis)
        self.assertIsInstance(report_saved, bool)

if __name__ == "__main__":
    unittest.main()