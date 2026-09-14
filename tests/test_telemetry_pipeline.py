import unittest
from unittest.mock import patch, MagicMock
import io

from skills.telemetry_pipeline import TelemetryPipelineOptimizer


class TestTelemetryPipeline(unittest.TestCase):

    def setUp(self):
        with patch('skills.system_telemetry.SystemTelemetry.__init__', return_value=None), \
             patch('skills.error_pipeline.ErrorPipeline.__init__', return_value=None):
            self.pipeline_optimizer = TelemetryPipelineOptimizer()

    def test_composition_initialization(self):
        self.assertIsNotNone(self.pipeline_optimizer)
        self.assertTrue(hasattr(self.pipeline_optimizer, 'telemetry'))
        self.assertTrue(hasattr(self.pipeline_optimizer, 'error_pipeline'))

    def test_run_telemetry_pipeline_success(self):
        with patch('skills.error_pipeline.ErrorPipeline.run_pipeline', return_value=True) as mock_run:
            result = self.pipeline_optimizer.run_telemetry_pipeline("test_log.log")
            self.assertTrue(result)
            mock_run.assert_called_once_with("test_log.log")

    def test_run_telemetry_pipeline_failure(self):
        with patch('skills.error_pipeline.ErrorPipeline.run_pipeline', return_value=False) as mock_run:
            result = self.pipeline_optimizer.run_telemetry_pipeline("test_log.log")
            self.assertFalse(result)
            mock_run.assert_called_once_with("test_log.log")

    def test_process_telemetry_stream(self):
        stream_data = io.BytesIO(b'telemetry stream bytes')
        with patch('skills.error_pipeline.ErrorPipeline.process_stream_pipeline', return_value=True) as mock_stream, \
             patch('skills.system_telemetry.process_stream_data') as mock_sys_stream:

            result = self.pipeline_optimizer.process_telemetry_stream(stream_data)
            self.assertTrue(result)
            mock_sys_stream.assert_called_once()
            mock_stream.assert_called_once()

    def test_process_telemetry_stream_failure(self):
        stream_data = io.BytesIO(b'bad stream')
        with patch('skills.error_pipeline.ErrorPipeline.process_stream_pipeline', return_value=False) as mock_stream, \
             patch('skills.system_telemetry.process_stream_data') as mock_sys_stream:

            result = self.pipeline_optimizer.process_telemetry_stream(stream_data)
            self.assertFalse(result)
            mock_sys_stream.assert_called_once()
            mock_stream.assert_called_once()

    def test_verify_and_optimize_success(self):
        url = "http://example.com/health"
        with patch('skills.error_pipeline.ErrorPipeline.verify_pipeline_fix', return_value=True) as mock_verify:
            result = self.pipeline_optimizer.verify_and_optimize(url)
            self.assertTrue(result)
            mock_verify.assert_called_once_with(url)

    def test_verify_and_optimize_failure(self):
        url = "http://example.com/health"
        with patch('skills.error_pipeline.ErrorPipeline.verify_pipeline_fix', return_value=False) as mock_verify:
            result = self.pipeline_optimizer.verify_and_optimize(url)
            self.assertFalse(result)
            mock_verify.assert_called_once_with(url)

    def test_exception_handling_graceful(self):
        with patch('skills.error_pipeline.ErrorPipeline.run_pipeline', side_effect=Exception("Critical Failure")):
            result = self.pipeline_optimizer.run_telemetry_pipeline("invalid.log")
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()