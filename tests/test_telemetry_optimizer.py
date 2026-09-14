import unittest
from unittest.mock import patch, MagicMock
import io

from skills.telemetry_optimizer import TelemetryOptimizer


class TestTelemetryOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer = TelemetryOptimizer()

    def test_composition_imports(self):
        try:
            from skills import system_telemetry
            from skills import error_pipeline
        except ImportError as e:
            self.fail(f"Модуль телеметрии обязаан импортировать зависимости: {e}")

    def test_optimize_telemetry_pipeline_success(self):
        with patch('skills.error_pipeline.ErrorPipeline.run_pipeline', return_value=True) as mock_run:
            result = self.optimizer.optimize_pipeline("test_log_path.log")
            self.assertTrue(result)
            mock_run.assert_called_once()

    def test_optimize_telemetry_pipeline_failure(self):
        with patch('skills.error_pipeline.ErrorPipeline.run_pipeline', return_value=False) as mock_run:
            result = self.optimizer.optimize_pipeline("bad_log_path.log")
            self.assertFalse(result)
            mock_run.assert_called_once()

    def test_process_stream_telemetry_success(self):
        stream_mock = io.BytesIO(b'some telemetry data stream')
        with patch('skills.system_telemetry.process_stream_data', return_value=True) as mock_process:
            result = self.optimizer.process_telemetry_stream(stream_mock)
            self.assertTrue(result)
            mock_process.assert_called_once()

    def test_process_stream_telemetry_failure(self):
        stream_mock = io.BytesIO(b'corrupted telemetry stream')
        with patch('skills.system_telemetry.process_stream_data', return_value=False) as mock_process:
            result = self.optimizer.process_telemetry_stream(stream_mock)
            self.assertFalse(result)
            mock_process.assert_called_once()

    def test_optimizer_exception_handling(self):
        stream_mock = io.BytesIO(b'error prone stream')
        with patch('skills.system_telemetry.process_stream_data', side_effect=Exception("Critical Telemetry Error")):
            result = self.optimizer.process_telemetry_stream(stream_mock)
            self.assertFalse(result)

    def test_verify_optimization_fix_via_web(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = self.optimizer.verify_optimization("http://localhost/health")
            self.assertTrue(result)

    def test_verify_optimization_fix_via_web_fail(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            result = self.optimizer.verify_optimization("http://localhost/health")
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()