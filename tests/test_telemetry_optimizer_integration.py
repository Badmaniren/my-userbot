import unittest
from skills.telemetry_optimizer import TelemetryOptimizer
from skills.system_telemetry import SystemTelemetry
from skills.error_pipeline import ErrorPipeline

class TestTelemetryOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.optimizer = TelemetryOptimizer()
        self.telemetry = SystemTelemetry()
        self.pipeline = ErrorPipeline()

    def test_telemetry_optimizer_composition(self):
        self.assertIsInstance(self.optimizer, TelemetryOptimizer)
        self.assertIsInstance(self.telemetry, SystemTelemetry)
        self.assertIsInstance(self.pipeline, ErrorPipeline)

    def test_optimizer_pipeline_execution(self):
        test_log_path = "test_system.log"
        with open(test_log_path, "w") as f:
            f.write("INFO: System started\n")
            
        result = self.pipeline.run_pipeline(test_log_path)
        self.assertIsInstance(result, bool)

    def test_optimizer_stream_processing(self):
        stream_data = {"metric": "CPU_USAGE", "value": 95}
        result = self.pipeline.process_stream_pipeline(stream_data)
        self.assertIsInstance(result, bool)

if __name__ == "__main__":
    unittest.main()