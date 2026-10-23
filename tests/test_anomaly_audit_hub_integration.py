import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.log_path = os.path.join(self.test_dir, f"audit_log_{uuid.uuid4().hex}.json")
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_audit_lifecycle_integration(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        severity = random.choice(severity_levels)

        metric_name = f"cpu_load_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)

        details = {
            "error_code": random.randint(1000, 9999),
            "message": f"Random failure event {uuid.uuid4()}"
        }

        telemetry_snapshot = {
            "memory_usage": round(random.uniform(10.0, 95.0), 2),
            "active_threads": random.randint(1, 256)
        }

        log_result = self.audit_hub.log_anomaly(
            source=source_id,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        self.assertIsNotNone(log_result)

        agg_result = self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )
        self.assertIsNotNone(agg_result)

        final_report = self.audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)

        self.assertTrue(os.path.exists(self.log_path), "Log file must be physically created during integration.")

if __name__ == "__main__":
    unittest.main()