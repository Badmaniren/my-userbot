import unittest
from skills.telemetry_pipeline import TelemetryPipeline
from skills.system_telemetry import SystemTelemetry
from skills.error_pipeline import ErrorPipeline

class TestTelemetryPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.pipeline = TelemetryPipeline()
        self.telemetry = SystemTelemetry()
        self.error_pipeline = ErrorPipeline()

    def test_composition_and_execution(self):
        self.assertIsInstance(self.pipeline, TelemetryPipeline)
        self.assertIsInstance(self.telemetry, SystemTelemetry)
        self.assertIsInstance(self.error_pipeline, ErrorPipeline)

        test_stream = {"metric": "CPU_usage", "value": 95.5, "error_sig": "MemoryError"}

        if hasattr(self.pipeline, "process_stream_data"):
            result = self.pipeline.process_stream_data(test_stream)
            self.assertIsInstance(result, bool)

if __name__ == "__main__":
    unittest.main()