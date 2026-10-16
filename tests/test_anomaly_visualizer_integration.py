import unittest
import uuid
import random
import os
import tempfile
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyVisualizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, f"anomalies_{uuid.uuid4()}.json")
        self.logger = AnomalyLogger(log_path=self.log_path)
        self.visualizer = AnomalyVisualizer()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_visualizer_integration_with_logger(self):
        random_source = f"service_{uuid.uuid4()}"
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_details = f"Test failure signature {uuid.uuid4()}"
        random_telemetry = {"cpu_load": random.random(), "memory_free": uuid.uuid4().hex}

        self.logger.log_anomaly(
            source=random_source,
            severity=random_severity,
            details=random_details,
            telemetry_snapshot=random_telemetry
        )

        anomalies = self.logger.get_anomalies()
        self.assertGreaterEqual(len(anomalies), 1, "Логгер должен содержать как минимум одну записанную аномалию.")

        visualization_result = self.visualizer.visualize_digest(anomalies)

        self.assertIsNotWithOrNone = visualization_result is not None
        
        if isinstance(visualization_result, str):
            self.assertIn(random_source, visualization_result)
            self.assertIn(random_severity, visualization_result)
        elif isinstance(visualization_result, dict):
            self.assertTrue(len(visualization_result) > 0)
        else:
            self.fail(f"Неизвестный формат визуализации: {type(visualization_result)}")

if __name__ == "__main__":
    unittest.main()