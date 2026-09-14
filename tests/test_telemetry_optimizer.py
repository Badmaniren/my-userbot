import unittest
from unittest.mock import patch
import io

from skills.telemetry_optimizer import TelemetryOptimizer
from skills import system_telemetry, error_pipeline

class TestTelemetryOptimizer(unittest.TestCase):

    def setUp(self):
        self.optimizer = TelemetryOptimizer()

    def test_composition_imports(self):
        self.assertTrue(hasattr(system_telemetry, 'SystemTelemetry'))
        self.assertTrue(hasattr(error_pipeline, 'ErrorPipeline'))

    def test_optimize_pipeline_success(self):
        with patch('skills.telemetry_optimizer.SystemTelemetry') as mock_telemetry, \
             patch('skills.telemetry_optimizer.ErrorPipeline') as mock_pipeline:

            mock_telemetry_instance = mock_telemetry.return_value
            mock_pipeline_instance = mock_pipeline.return_value
            mock_pipeline_instance.run_pipeline.return_value = True

            result = self.optimizer.optimize_pipeline("metrics.log")
            self.assertTrue(result)

    def test_optimize_pipeline_failure(self):
        with patch('skills.telemetry_optimizer.SystemTelemetry') as mock_telemetry, \
             patch('skills.telemetry_optimizer.ErrorPipeline') as mock_pipeline:

            mock_telemetry_instance = mock_telemetry.return_value
            mock_pipeline_instance = mock_pipeline.return_value
            mock_pipeline_instance.run_pipeline.return_value = False

            result = self.optimizer.optimize_pipeline("invalid_metrics.log")
            self.assertFalse(result)

    def test_process_stream_optimization(self):
        with patch('skills.telemetry_optimizer.SystemTelemetry') as mock_telemetry, \
             patch('skills.telemetry_optimizer.ErrorPipeline') as mock_pipeline:

            mock_telemetry_instance = mock_telemetry.return_value
            mock_pipeline_instance = mock_pipeline.return_value
            mock_pipeline_instance.process_stream_pipeline.return_value = True

            stream_data = io.BytesIO(b'some telemetry stream data')
            result = self.optimizer.process_stream_optimization(stream_data)
            self.assertTrue(result)

    def test_process_stream_optimization_fail(self):
        with patch('skills.telemetry_optimizer.SystemTelemetry') as mock_telemetry, \
             patch('skills.telemetry_optimizer.ErrorPipeline') as mock_pipeline:

            mock_telemetry_instance = mock_telemetry.return_value
            mock_pipeline_instance = mock_pipeline.return_value
            mock_pipeline_instance.process_stream_pipeline.return_value = False

            stream_data = io.BytesIO(b'corrupted stream data')
            result = self.optimizer.process_stream_optimization(stream_data)
            self.assertFalse(result)

    def test_analyze_performance_exception_handling(self):
        with patch('skills.telemetry_optimizer.SystemTelemetry', side_effect=Exception("Telemetry Error")):
            result = self.optimizer.optimize_pipeline("metrics.log")
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()