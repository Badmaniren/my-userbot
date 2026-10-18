import unittest
import uuid
import random
import tempfile
import os

from skills.patch_metric_collector import (
    anomaly_filter,
    anomaly_logger,
    git_inspector
)

class TestPatchMetricCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, f"test_anomaly_{uuid.uuid4()}.log")
        self.repo_path = os.getcwd()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_metric_collector_integration_flow(self):
        random_source = f"source_{uuid.uuid4().hex[:8]}"
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_details = f"Integration test anomaly payload {uuid.uuid4()}"
        random_telemetry = {
            "metric_id": str(uuid.uuid4()),
            "value": random.random() * 100
        }

        logger = anomaly_logger.AnomalyLogger(log_path=self.log_path)

        logger.log_anomaly(
            source=random_source,
            severity=random_severity,
            details=random_details,
            telemetry_snapshot=random_telemetry
        )

        anomalies = logger.get_anomalies()
        self.assertIsInstance(anomalies, list)
        self.assertGreaterEqual(len(anomalies), 1)

        structured_report = logger.get_structured_report()
        self.assertIsNotNone(structured_report)

        filtered_data = anomaly_filter.start_new(anomalies)
        self.assertIsNotNone(filtered_data)

        inspector = git_inspector.GitInspector(repo_path=self.repo_path)
        repo_analysis = inspector.analyze_repository()
        self.assertIsNotNone(repo_analysis)

        logger.clear_logs()
        self.assertEqual(len(logger.get_anomalies()), 0)
        self.assertFalse(os.path.exists(self.log_path))

if __name__ == "__main__":
    unittest.main()