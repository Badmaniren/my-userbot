import unittest
import uuid
import random
import tempfile
import os
from skills.anomaly_autofixer_engine import autofix_anomaly
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyAutofixerEngineIntegration(unittest.TestCase):
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

    def test_autofixer_engine_integration_flow(self):
        anomaly_source = f"service_{uuid.uuid4().hex[:8]}"
        severity_levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        severity = random.choice(severity_levels)

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.uniform(10.0, 100.0)

        telemetry_snapshot = {
            "cpu_load": random.randint(50, 100),
            "memory_usage": random.randint(1024, 8192),
            "random_seed": str(uuid.uuid4())
        }

        details = {
            "error_code": random.randint(500, 599),
            "description": f"Integration test anomaly description {uuid.uuid4()}"
        }

        self.audit_hub.log_anomaly(
            source=anomaly_source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=metric_value
        )

        fix_result = autofix_anomaly(
            source=anomaly_source,
            severity=severity,
            details=details,
            telemetry=telemetry_snapshot
        )

        self.assertIsNotNone(fix_result)
        self.assertIn("status", fix_result)

        anomalies_logged = self.logger.get_anomalies()
        self.assertGreaterEqual(len(anomalies_logged), 1)

        final_report = self.audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)

        self.assertTrue(os.path.exists(self.log_path))

if __name__ == "__main__":
    unittest.main()