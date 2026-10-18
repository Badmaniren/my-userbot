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
        
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_integration_logging_and_aggregation(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(0.0, 100.0), 2)
        
        details = {
            "error_code": random.randint(1000, 9999),
            "description": f"Random failure event {uuid.uuid4().hex}"
        }
        telemetry_snapshot = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 1),
            "memory_free": random.randint(1024, 8192)
        }

        log_result = self.hub.log_anomaly(
            source=source_id,
            severity=severity_level,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        
        self.assertTrue(os.path.exists(self.log_path), "Log file must be created on disk without silent suppression.")

        agg_result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        final_report = self.hub.generate_final_report()

        self.assertIsNotNone(final_report)
        self.assertIsInstance(final_report, (dict, list, str))

if __name__ == "__main__":
    unittest.main()