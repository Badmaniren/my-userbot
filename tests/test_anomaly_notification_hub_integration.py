import unittest
import os
import tempfile
import uuid
import random

from skills.anomaly_notification_hub import anomaly_alert_dispatcher
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger


class TestAnomalyNotificationHubIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4()}.log")
        self.repo_path = self.test_dir.name
        self.threshold = random.uniform(0.5, 0.9)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.logger = AnomalyLogger(log_path=self.log_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_notification_hub_integration_workflow(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.uniform(10.0, 100.0)

        details = {
            "error_code": random.randint(500, 599),
            "description": f"Random failure token: {uuid.uuid4()}"
        }
        telemetry_snapshot = {
            "cpu_load": random.uniform(10.0, 99.0),
            "memory_free": random.randint(1024, 8192)
        }

        self.audit_hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        final_report = self.audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)

        logged_anomalies = self.logger.get_anomalies()
        self.assertIsInstance(logged_anomalies, list)
        self.assertTrue(len(logged_anomalies) > 0)

        found = False
        for anomaly in logged_anomalies:
            if anomaly.get("source") == source_id:
                found = True
                self.assertEqual(anomaly.get("severity"), severity_level)
                self.assertEqual(anomaly.get("details"), details)
                break

        self.assertTrue(found, "Logged anomaly with generated source ID was not found in AnomalyLogger records.")

        structured_report = self.logger.get_structured_report()
        self.assertIsNotNone(structured_report)

        self.assertTrue(os.path.exists(self.log_path), "Audit log file was not successfully created on disk.")


if __name__ == "__main__":
    unittest.main()