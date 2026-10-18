import unittest
import uuid
import random
import tempfile
import os

from skills. anomaly_reactor import anomaly_reactor
from skills. anomaly_logger import AnomalyLogger


class TestIntegrationAnomalyReactor(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.tmp_dir.name, f"anomaly_log_{uuid.uuid4()}.json")
        self.logger = AnomalyLogger(log_path=self.log_path)
        self.logger.clear_logs()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_autonomous_reaction_integration(self):
        source_id = f"service-{uuid.uuid4()}"
        severity_level = random.randint(1, 10)
        telemetry_data = {
            "cpu_load": random.uniform(85.0, 99.9),
            "memory_leak_mb": random.randint(500, 2048),
            "request_id": str(uuid.uuid4())
        }
        details_msg = f"Integration test anomaly payload {uuid.uuid4()}"

        self.logger.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        anomalies = self.logger.get_anomalies()
        self.assertGreaterEqual(len(anomalies), 1)

        latest_anomaly = anomalies[-1]
        self.assertEqual(latest_anomaly.get("source"), source_id)
        self.assertEqual(latest_anomaly.get("severity"), severity_level)

        reaction_result = anomaly_reactor.handle_anomaly(latest_anomaly)

        self.assertIsNotNone(reaction_result)
        structured_report = self.logger.get_structured_report()
        self.assertIn(source_id, str(structured_report))

if __name__ == "__main__":
    unittest.main()