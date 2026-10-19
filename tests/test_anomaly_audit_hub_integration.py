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
        self.log_path = os.path.join(self.test_dir, f"anomaly_log_{uuid.uuid4().hex}.json")
        self.threshold = round(random.uniform(0.1, 0.9), 2)
        
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_audit_workflow_integration(self):
        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        unique_detail_key = f"key_{uuid.uuid4().hex[:6]}"
        unique_detail_val = str(uuid.uuid4())
        details = {unique_detail_key: unique_detail_val}

        telemetry_metric = f"cpu_load_{random.randint(1, 100)}"
        telemetry_val = round(random.uniform(10.0, 99.9), 2)
        telemetry_snapshot = {telemetry_metric: telemetry_val}

        log_res = self.audit_hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.assertIsNotNone(log_res)
        self.assertTrue(os.path.exists(self.log_path))

        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = round(random.uniform(0.0, 10.0), 2)
        
        aggregate_res = self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        self.assertIsNotNone(aggregate_res)

        final_report = self.audit_hub.generate_final_report()

        self.assertIsNotNone(final_report)

        with open(self.log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
            self.assertIn(source_name, log_content)
            self.assertIn(unique_detail_val, log_content)


if __name__ == "__main__":
    unittest.main()