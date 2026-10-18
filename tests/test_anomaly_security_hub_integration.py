import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.anomaly_security_hub import AnomalySecurityHub


class TestAnomalySecurityHubIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "repo")
        self.log_path = os.path.join(self.test_dir, "logs")
        os.makedirs(self.repo_path, exist_ok=True)
        os.makedirs(self.log_path, exist_ok=True)

        self.threshold = random.uniform(0.5, 0.9)
        self.hub = AnomalySecurityHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_security_hub_composition_and_logging(self):
        unique_source = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_msg = f"Security breach attempt detected: {uuid.uuid4().hex}"

        telemetry_data = {
            "cpu_load": random.uniform(10.0, 99.9),
            "memory_usage": random.randint(1024, 8192),
            "request_id": uuid.uuid4().hex
        }

        self.hub.log_anomaly(
            source=unique_source,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        report = self.hub.get_structured_report()
        self.assertIsNotNone(report)

        anomalies = self.hub.get_anomalies()
        self.assertIsInstance(anomalies, list)

        found = False
        for anomaly in anomalies:
            if anomaly.get("source") == unique_source and anomaly.get("details") == details_msg:
                found = True
                self.assertEqual(anomaly.get("severity"), severity_level)
                self.assertEqual(anomaly.get("telemetry_snapshot"), telemetry_data)
                break

        self.assertTrue(found, "Записанная аномалия не найдена через компоненты логирования.")

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.randint(100, 1000)
        aggregated = self.hub.aggregate_and_report(metric_name=metric_name, value=metric_value)
        self.assertIsNotNone(aggregated)

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report)

        self.hub.clear_logs()
        cleared_anomalies = self.hub.get_anomalies()
        self.assertEqual(len(cleared_anomalies), 0, "Логи не были очищены.")


if __name__ == "__main__":
    unittest.main()