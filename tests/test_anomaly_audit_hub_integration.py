import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_file = os.path.join(self.repo_path, f"audit_{uuid.uuid4()}.log")
        
        self.threshold = round(random.uniform(0.1, 9.9), 2)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_anomaly_audit_hub_integration_workflow(self):
        unique_source = f"source_{uuid.uuid4().hex[:8]}"
        severity_levels = ["INFO", "WARNING", "CRITICAL", "ERROR"]
        selected_severity = random.choice(severity_levels)
        
        random_id = str(uuid.uuid4())
        test_details = {
            "error_code": random.randint(1000, 9999),
            "identifier": random_id,
            "message": "Integration test anomaly payload"
        }

        telemetry_snapshot = {
            "cpu_load": round(random.uniform(0.0, 100.0), 2),
            "memory_free": random.randint(1024, 65535)
        }

        log_result = self.hub.log_anomaly(
            source=unique_source,
            severity=selected_severity,
            details=test_details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertIsNotNone(log_result)
        self.assertTrue(os.path.exists(self.log_file), "Лог-файл должен быть создан в процессе работы AnomalyLogger.")

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(self.threshold * 2.0 + 1.0, self.threshold * 2.0 + 50.0), 2)

        agg_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(agg_result)

        final_report = self.hub.generate_final_report()
        self.assertIsNotNone(final_report)

        report_str = str(final_report)
        self.assertIn(metric_name, report_str)
        self.assertIn(unique_source, report_str)
        self.assertIn(random_id, report_str)


if __name__ == "__main__":
    unittest.main()