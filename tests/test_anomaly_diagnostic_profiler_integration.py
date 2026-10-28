import unittest
import os
import shutil
import uuid
import random
from skills.anomaly_diagnostic_profiler import anomaly_audit_hub, anomaly_logger

class TestAnomalyDiagnosticProfilerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.repo_path = f"./test_repo_{self.test_id}"
        self.log_path = f"./test_logs_{self.test_id}"

        os.makedirs(self.repo_path, exist_ok=True)
        os.makedirs(self.log_path, exist_ok=True)

        self.threshold = random.uniform(0.5, 0.9)
        self.audit_hub = anomaly_audit_hub.AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.logger = anomaly_logger.AnomalyLogger(log_path=self.log_path)

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)
        if os.path.exists(self.log_path):
            shutil.rmtree(self.log_path)

    def test_audit_hub_and_logger_integration(self):
        source = f"service_{uuid.uuid4()}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric_name = f"cpu_load_{uuid.uuid4()}"
        metric_value = random.uniform(10.0, 99.9)

        details = {
            "error_code": random.randint(500, 599),
            "message": f"Random system failure {uuid.uuid4()}"
        }
        telemetry_snapshot = {
            "memory_usage": random.uniform(20.0, 90.0),
            "active_threads": random.randint(10, 500)
        }

        self.audit_hub.log_anomaly(
            source=source,
            severity=severity,
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

        structured_report = self.logger.get_structured_report()
        self.assertIsNotNone(structured_report)

        self.logger.clear_logs()
        cleared_anomalies = self.logger.get_anomalies()
        self.assertEqual(len(cleared_anomalies), 0)

if __name__ == "__main__":
    unittest.main()