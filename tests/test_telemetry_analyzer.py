import unittest
from unittest.mock import patch
import io

from skills.telemetry_analyzer import TelemetryAnalyzer


class TestTelemetryAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = TelemetryAnalyzer()

    def test_composition_imports(self):
        with patch('skills.telemetry_analyzer.SystemTelemetry') as mock_telemetry, \
             patch('skills.telemetry_analyzer.ErrorAnalyzer') as mock_error_analyzer:

            instance_telemetry = mock_telemetry.return_value
            instance_error = mock_error_analyzer.return_value

            analyzer = TelemetryAnalyzer()
            res = analyzer.analyze_system_health("test_path.log")
            self.assertIsInstance(res, bool)

    def test_analyze_system_health_success(self):
        with patch('skills.telemetry_analyzer.SystemTelemetry') as mock_telemetry, \
             patch('skills.telemetry_analyzer.ErrorAnalyzer') as mock_error_analyzer:

            instance_error = mock_error_analyzer.return_value
            instance_error.parse_log.return_value = True
            instance_error.analyze_and_prevent.return_value = True

            analyzer = TelemetryAnalyzer()
            res = analyzer.analyze_system_health("dummy.log")
            self.assertTrue(res)

    def test_analyze_system_health_failure(self):
        with patch('skills.telemetry_analyzer.SystemTelemetry') as mock_telemetry, \
             patch('skills.telemetry_analyzer.ErrorAnalyzer') as mock_error_analyzer:

            instance_error = mock_error_analyzer.return_value
            instance_error.parse_log.return_value = False

            analyzer = TelemetryAnalyzer()
            res = analyzer.analyze_system_health("bad.log")
            self.assertFalse(res)

    def test_process_telemetry_stream(self):
        with patch('skills.telemetry_analyzer.process_stream_data') as mock_process, \
             patch('skills.telemetry_analyzer.ErrorAnalyzer') as mock_error_analyzer:

            mock_process.return_value = True
            instance_error = mock_error_analyzer.return_value
            instance_error.process_stream.return_value = True

            stream_mock = io.BytesIO(b'telemetry stream data')
            analyzer = TelemetryAnalyzer()
            res = analyzer.process_telemetry_stream(stream_mock)
            self.assertTrue(res)

    def test_process_telemetry_stream_exception_handling(self):
        with patch('skills.telemetry_analyzer.process_stream_data') as mock_process:
            mock_process.side_effect = Exception("Stream failure")

            stream_mock = io.BytesIO(b'broken stream')
            res = self.analyzer.process_telemetry_stream(stream_mock)
            self.assertFalse(res)

    def test_complex_metrics_generation(self):
        with patch('skills.telemetry_analyzer.SystemTelemetry') as mock_telemetry, \
             patch('skills.telemetry_analyzer.analyze_errors') as mock_analyze:

            mock_analyze.return_value = "Critical metrics report"
            res = self.analyzer.generate_complex_metrics("metrics.log")
            self.assertIsInstance(res, bool)
            self.assertTrue(res)