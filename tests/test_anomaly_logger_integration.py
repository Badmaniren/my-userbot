import unittest
import os
import json
import uuid
import random
from skills.anomaly_logger import AnomalyLogger
from skills.system_telemetry import SystemTelemetry


class TestAnomalyLoggerIntegration(unittest.TestCase):

    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.log_file = f"test_anomalies_{self.rand_suffix}.jsonl"
        self.logger = AnomalyLogger(log_path=self.log_file)

    def tearDown(self):
        self.logger.clear_logs()
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

    def test_log_anomaly_and_report_integration(self):
        random_source = f"source_module_{uuid.uuid4().hex[:6]}"
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_detail_key = f"key_{uuid.uuid4().hex[:4]}"
        random_detail_val = random.randint(100, 999)
        
        details = {random_detail_key: random_detail_val}
        telemetry_snapshot = {"cpu_load": random.uniform(0.1, 0.9)}

        self.logger.log_anomaly(
            source=random_source,
            severity=random_severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertTrue(os.path.exists(self.log_file))

        report = self.logger.get_structured_report()
        self.assertIsInstance(report, list)
        self.assertEqual(len(report), 1)

        logged_entry = report[0]
        self.assertEqual(logged_entry["source"], random_source)
        self.assertEqual(logged_entry["severity"], random_severity)
        self.assertEqual(logged_entry["details"][random_detail_key], random_detail_val)
        self.assertEqual(logged_entry["telemetry_snapshot"], telemetry_snapshot)
        self.assertIn("id", logged_entry)

        anomalies = self.logger.get_anomalies()
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["id"], logged_entry["id"])

    def test_log_anomaly_with_dict_source_integration(self):
        random_id = str(uuid.uuid4())
        random_source = f"dict_source_{uuid.uuid4().hex[:6]}"
        random_severity = random.choice(["INFO", "WARNING", "ERROR"])
        
        source_dict = {
            "id": random_id,
            "source": random_source,
            "severity": random_severity,
            "details": {"test_run": random.randint(1, 50)}
        }

        random_telemetry = {"memory_usage": random.randint(1024, 8192)}

        self.logger.log_anomaly(source=source_dict, telemetry_snapshot=random_telemetry)

        report = self.logger.get_structured_report()
        self.assertEqual(len(report), 1)

        logged_entry = report[0]
        self.assertEqual(logged_entry["id"], random_id)
        self.assertEqual(logged_entry["source"], random_source)
        self.assertEqual(logged_entry["severity"], random_severity)
        self.assertEqual(logged_entry["telemetry_snapshot"], random_telemetry)

    def test_clear_logs_integration(self):
        random_source = f"temp_source_{uuid.uuid4().hex[:6]}"
        self.logger.log_anomaly(source=random_source, severity="LOW", details={"val": random.random()})
        
        self.assertTrue(os.path.exists(self.log_file))
        self.assertTrue(len(self.logger.get_structured_report()) > 0)

        self.logger.clear_logs()
        self.assertFalse(os.path.exists(self.log_file))
        self.assertEqual(self.logger.get_structured_report(), [])


if __name__ == "__main__":
    unittest.main()