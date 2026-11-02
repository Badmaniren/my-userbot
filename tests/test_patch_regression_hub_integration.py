import unittest
import uuid
import random
import os
from skills.patch_regression_hub import AnomalyAuditHub, start_new

class TestPatchRegressionHubIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = str(uuid.uuid4())
        self.log_filename = f"test_log_{self.unique_id}.json"
        self.repo_dir = f"test_repo_{self.unique_id}"
        os.makedirs(self.repo_dir, exist_ok=True)
        self.threshold_val = round(random.uniform(0.1, 0.9), 2)

    def tearDown(self):
        if os.path.exists(self.log_filename):
            try:
                os.remove(self.log_filename)
            except OSError:
                pass
        if os.path.exists(self.repo_dir):
            try:
                os.rmdir(self.repo_dir)
            except OSError:
                pass

    def test_anomaly_audit_hub_full_cycle(self):
        hub = AnomalyAuditHub(repo_path=self.repo_dir, log_path=self.log_filename, threshold=self.threshold_val)
        
        source_name = f"source_{uuid.uuid4()}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_text = f"Details for anomaly {uuid.uuid4()}"
        snapshot = {"metric_key": random.randint(100, 999)}

        hub.log_anomaly(source=source_name, severity=severity_level, details=details_text, telemetry_snapshot=snapshot)

        metric_name = f"metric_{uuid.uuid4()}"
        metric_value = round(random.uniform(1.0, 100.0), 2)
        
        agg_result = hub.aggregate_and_report(metric_name=metric_name, value=metric_value)
        self.assertIsInstance(agg_result, dict)
        self.assertTrue(agg_result.get("aggregated"))
        self.assertEqual(agg_result.get("score"), metric_value)
        self.assertEqual(agg_result.get("metric_name"), metric_name)
        self.assertGreaterEqual(agg_result.get("total_anomalies"), 1)

        final_report = hub.generate_final_report()
        self.assertIsInstance(final_report, dict)
        self.assertEqual(final_report.get("status"), "verified")
        self.assertEqual(final_report.get("code"), "success")
        self.assertGreaterEqual(final_report.get("anomalies_count"), 1)

    def test_start_new_with_payload_id(self):
        payload_id = f"payload_{uuid.uuid4()}"
        target_name = f"target_{uuid.uuid4()}"
        error_rate_val = round(random.uniform(0.0, 1.0), 4)
        severity_level = random.choice(["LOW", "HIGH"])

        dynamic_data = {
            "repo_path": self.repo_dir,
            "log_path": self.log_filename,
            "threshold": self.threshold_val,
            "payload_id": payload_id,
            "severity_level": severity_level,
            "target": target_name,
            "error_rate": error_rate_val
        }

        result = start_new(dynamic_data)
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("aggregated"))
        self.assertEqual(result.get("score"), error_rate_val)
        self.assertEqual(result.get("metric_name"), target_name)

    def test_start_new_with_string_anomalies_and_numeric(self):
        target_name = f"target_{uuid.uuid4()}"
        numeric_metric_val = round(random.uniform(10.0, 50.0), 2)
        random_key = f"key_{uuid.uuid4()}"
        random_str_value = f"anomaly_desc_{uuid.uuid4()}"

        dynamic_data = {
            "repo_path": self.repo_dir,
            "log_path": self.log_filename,
            "threshold": self.threshold_val,
            "target": target_name,
            "numeric_metric": numeric_metric_val,
            random_key: random_str_value
        }

        result = start_new(dynamic_data)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "verified")
        self.assertEqual(result.get("code"), "success")
        self.assertGreaterEqual(result.get("anomalies_count"), 1)

    def test_start_new_stream_source(self):
        token_val = f"token_{uuid.uuid4()}"
        dynamic_data = {
            "repo_path": self.repo_dir,
            "stream_source": True,
            "token": token_val
        }

        result = start_new(dynamic_data)
        self.assertIsInstance(result, dict)
        self.assertIn("token", result)
        self.assertEqual(result["token"], token_val)

if __name__ == "__main__":
    unittest.main()