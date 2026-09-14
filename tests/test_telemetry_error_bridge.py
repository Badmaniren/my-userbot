import unittest
from unittest.mock import patch, MagicMock
import io

from skills.telemetry_error_bridge import TelemetryErrorBridge


class TestTelemetryErrorBridge(unittest.TestCase):

    def setUp(self):
        self.bridge = TelemetryErrorBridge()

    def test_bridge_initialization(self):
        self.assertIsNotNone(self.bridge)

    def test_process_telemetry_and_errors_success(self):
        with patch('skills.system_telemetry.process_stream_data') as mock_telemetry, \
             patch('skills.error_pipeline.ErrorPipeline.process_stream_pipeline') as mock_pipeline:
            
            mock_telemetry.return_value = True
            mock_pipeline.return_value = True

            stream = io.BytesIO(b'telemetry_and_error_stream_data')
            result = self.bridge.process_telemetry_and_errors(stream)
            self.assertTrue(result)

    def test_process_telemetry_and_errors_failure(self):
        with patch('skills.system_telemetry.process_stream_data') as mock_telemetry, \
             patch('skills.error_pipeline.ErrorPipeline.process_stream_pipeline') as mock_pipeline:
            
            mock_telemetry.return_value = False
            mock_pipeline.return_value = False

            stream = io.BytesIO(b'bad_stream_data')
            result = self.bridge.process_telemetry_and_errors(stream)
            self.assertFalse(result)

    def test_bridge_handles_exceptions_gracefully(self):
        with patch('skills.system_telemetry.process_stream_data', side_effect=Exception("Telemetry Failure")):
            stream = io.BytesIO(b'exception_stream')
            result = self.bridge.process_telemetry_and_errors(stream)
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()