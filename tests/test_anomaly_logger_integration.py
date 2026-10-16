import unittest
import uuid
import random
import os
import tempfile
from skills.anomaly_logger import AnomalyLogger
from skills.system_telemetry import SystemTelemetry

class TestAnomalyLoggerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"anomaly_{uuid.uuid4().hex}.json")
        self.logger = AnomalyLogger(log_path=self.log_file)
        self.telemetry = SystemTelemetry()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_anomaly_logger_integration_flow(self):
        random_id = str(uuid.uuid4())
        metric_value = random.uniform(100.0, 1000.0)
        anomaly_payload = {
            "anomaly_id": random_id,
            "metric": "cpu_load",
            "value": metric_value,
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        }

        telemetry_data = self.telemetry.collect_metrics() if hasattr(self.telemetry, "collect_metrics") else {"status": "active"}
        
        self.logger.log_anomaly(anomaly_payload, telemetry_snapshot=telemetry_data)

        self.assertTrue(os.path.exists(self.log_file), "Файл лога аномалий не был создан.")

        stored_anomalies = self.logger.get_anomalies()
        found = False
        for anomaly in stored_anomalies:
            if anomaly.get("anomaly_id") == random_id:
                found = True
                self.assertEqual(anomaly["value"], metric_value)
                self.assertIn("telemetry_snapshot", anomaly)

        self.assertTrue(found, f"Аномалия с ID {random_id} не найдена в хранилище логов.")

if __name__ == "__main__":
    unittest.main()