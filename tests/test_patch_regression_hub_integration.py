import unittest
import uuid
import random
import tempfile
import os
from skills.patch_regression_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.git_inspector import GitInspector

class TestPatchRegressionHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.test_dir.name, f"anomaly_{uuid.uuid4().hex}.log")
        self.repo_path = self.test_dir.name
        self.threshold = random.uniform(0.1, 0.9)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_regression_hub_integration_workflow(self):
        audit_hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_file, threshold=self.threshold)
        logger = AnomalyLogger(log_path=self.log_file)
        inspector = GitInspector(repo_path=self.repo_path)

        source_name = f"source_{uuid.uuid4().hex[:8]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_msg = f"Test anomaly detail message {uuid.uuid4()}"
        telemetry_data = {"cpu_load": random.random(), "memory_usage": random.randint(100, 500)}

        audit_hub.log_anomaly(
            source=source_name,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        logged_anomalies = logger.get_anomalies()
        self.assertGreaterEqual(len(logged_anomalies), 1, "Anomaly should be logged successfully.")
        
        found = False
        for anomaly in logged_anomalies:
            if anomaly.get("source") == source_name and anomaly.get("details") == details_msg:
                found = True
                break
        self.assertTrue(found, "The exact logged anomaly must be retrievable via AnomalyLogger.")

        metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        metric_val = random.uniform(10.0, 100.0)
        aggregation_result = audit_hub.aggregate_and_report(metric_name=metric_key, value=metric_val)
        
        if aggregation_result is not None:
            self.assertIsInstance(aggregation_result, (dict, str, float, int))

        repo_analysis = inspector.analyze_repository()
        self.assertIsNotNone(repo_analysis, "GitInspector should successfully analyze the repository context.")

        final_report = audit_hub.generate_final_report()
        self.assertIsNotNone(final_report, "Final report generation should not return None.")
        
        self.assertTrue(os.path.exists(self.log_file), "The underlying log file must exist on disk.")

if __name__ == "__main__":
    unittest.main()