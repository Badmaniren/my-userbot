import unittest
import tempfile
import os
import uuid
import random

from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_forecaster import forecast_anomalies


class TestAnomalyForecasterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, f"anomalies_{uuid.uuid4()}.json")
        self.logger = AnomalyLogger(log_path=self.log_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_forecast_anomalies_integration(self):
        unique_source = f"service-{uuid.uuid4()}"
        random_severity = random.randint(1, 10)
        random_details = {"error_code": random.randint(500, 599), "trace_id": str(uuid.uuid4())}
        random_telemetry = {"cpu_load": random.uniform(80.0, 99.9), "memory_usage": random.randint(1024, 8192)}

        self.logger.log_anomaly(
            source=unique_source,
            severity=random_severity,
            details=random_details,
            telemetry_snapshot=random_telemetry
        )

        structured_report = self.logger.get_structured_report()
        self.assertIsNotNone(structured_report)

        forecast_result = forecast_anomalies(self.logger)

        self.assertIsNotNone(forecast_result)
        self.assertIn(unique_source, str(forecast_result))


if __name__ == "__main__":
    unittest.main()