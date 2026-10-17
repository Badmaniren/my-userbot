import unittest
import uuid
import random
import os
import tempfile
from skills.anomaly_filter import AnomalyFilter
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyFilterIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, f"test_log_{uuid.uuid4()}.json")
        self.logger = AnomalyLogger(log_path=self.log_path)
        self.filter_module = AnomalyFilter()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_anomaly_filter_and_logger_integration(self):
        unique_source = f"service_{uuid.uuid4()}"
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_error_code = random.randint(1000, 9999)
        
        raw_anomaly_data = {
            "source": unique_source,
            "severity": random_severity,
            "details": f"Generated test anomaly error code: {random_error_code}",
            "telemetry_snapshot": {
                "cpu_load": random.uniform(10.0, 99.9),
                "memory_usage": random.randint(512, 16384)
            }
        }

        filtered_data = self.filter_module.filter(raw_anomaly_data)
        
        self.assertIsNotNone(filtered_data, "Фильтр не должен возвращать None для валидных данных")
        self.assertEqual(filtered_data["source"], unique_source)
        self.assertEqual(filtered_data["severity"], random_severity)

        self.logger.log_anomaly(
            source=filtered_data["source"],
            severity=filtered_data["severity"],
            details=filtered_data["details"],
            telemetry_snapshot=filtered_data["telemetry_snapshot"]
        )

        anomalies = self.logger.get_anomalies()
        self.assertTrue(len(anomalies) > 0, "Логгер должен содержать записанные аномалии")
        
        latest_anomaly = anomalies[-1]
        self.assertEqual(latest_anomaly["source"], unique_source)
        self.assertEqual(latest_anomaly["severity"], random_severity)
        self.assertIn(str(random_error_code), latest_anomaly["details"])

        self.assertTrue(os.path.exists(self.log_path), "Файл лога должен быть физически создан на диске")

if __name__ == '__main__':
    unittest.main()