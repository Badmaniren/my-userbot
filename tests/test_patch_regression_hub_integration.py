import unittest
import uuid
import random
import tempfile
import os
from skills.patch_regression_hub import AnomalyAuditHub, start_new

class TestPatchRegressionHubIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, f"anomaly_log_{uuid.uuid4().hex}.json")
        self.repo_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_anomaly_audit_hub_full_cycle(self):
        random_threshold = round(random.uniform(0.1, 0.9), 2)
        random_source = f"source_{uuid.uuid4().hex[:8]}"
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_details = f"Details for test run {uuid.uuid4().hex}"
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(10.0, 100.0), 2)

        hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_file, threshold=random_threshold)
        
        hub.log_anomaly(
            source=random_source,
            severity=random_severity,
            details=random_details,
            telemetry_snapshot={"run_id": uuid.uuid4().hex}
        )

        aggregated = hub.aggregate_and_report(metric_name=metric_name, value=metric_value)
        self.assertTrue(aggregated.get("aggregated"))
        self.assertEqual(aggregated.get("score"), metric_value)
        self.assertEqual(aggregated.get("metric_name"), metric_name)
        self.assertGreaterEqual(aggregated.get("total_anomalies"), 1)

        final_report = hub.generate_final_report()
        self.assertEqual(final_report.get("status"), "verified")
        self.assertEqual(final_report.get("code"), "success")
        self.assertGreaterEqual(final_report.get("anomalies_count"), 1)

    def test_start_new_with_payload(self):
        payload_id = uuid.uuid4().hex
        severity = random.choice(["LOW", "HIGH"])
        target = f"target_{uuid.uuid4().hex[:4]}"
        error_rate = round(random.uniform(0.0, 1.0), 3)

        dynamic_input_data = {
            "payload_id": payload_id,
            "severity_level": severity,
            "target": target,
            "error_rate": error_rate,
            "repo_path": self.repo_path,
            "log_path": self.log_file
        }

        result = start_new(dynamic_input_data)
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("aggregated"))
        self.assertEqual(result.get("score"), error_rate)
        self.assertEqual(result.get("metric_name"), target)

    def test_start_new_with_string_metrics(self):
        random_key = f"key_{uuid.uuid4().hex[:6]}"
        random_val = f"val_{uuid.uuid4().hex}"
        numeric_metric = round(random.uniform(1.0, 50.0), 2)

        dynamic_input_data = {
            "repo_path": self.repo_path,
            "log_path": self.log_file,
            random_key: random_val,
            "numeric_metric": numeric_metric,
            "target": "integration_test_metric"
        }

        result = start_new(dynamic_input_data)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "verified")
        self.assertEqual(result.get("code"), "success")
        self.assertGreaterEqual(result.get("anomalies_count"), 1)

if __name__ == "__main__":
    unittest.main()