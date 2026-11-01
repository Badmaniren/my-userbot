import unittest
import uuid
import tempfile
import os
from skills.patch_regression_suite import PatchRegressionSuite, PatchRegressionSuiteError
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestPatchRegressionSuiteIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.temp_dir.name, "anomaly_test.log")
        self.audit_hub = AnomalyAuditHub(repo_path=self.temp_dir.name, log_path=self.log_path, threshold=5.0)
        self.logger = AnomalyLogger(log_path=self.log_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_regression_suite_execution_and_auditing(self):
        random_suite_id = uuid.uuid4().hex
        random_payload = f"patch_data_{uuid.uuid4().hex}"

        suite = PatchRegressionSuite(suite_id=random_suite_id)
        self.assertEqual(suite.suite_id, random_suite_id)
        self.assertFalse(suite.executed)

        result = suite.run_suite(patch_payload=random_payload)

        self.assertTrue(suite.executed)
        self.assertEqual(result["suite_id"], random_suite_id)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["payload_len"], len(random_payload))
        self.assertIn("signature", result)

        self.logger.log_anomaly(
            source="patch_regression_suite",
            severity=1,
            details=f"Suite {random_suite_id} executed successfully with payload len {len(random_payload)}",
            telemetry_snapshot={"suite_id": random_suite_id, "status": "passed"}
        )

        self.audit_hub.aggregate_and_report("regression_test_metric", 1.0)
        final_report = self.audit_hub.generate_final_report()

        logs = self.logger.get_anomalies()
        self.assertTrue(any(log["source"] == "patch_regression_suite" for log in logs))
        self.assertIsNotNone(final_report)

    def test_regression_suite_empty_payload_raises_error(self):
        suite = PatchRegressionSuite()
        with self.assertRaises(PatchRegressionSuiteError):
            suite.run_suite(patch_payload="")

        with self.assertRaises(PatchRegressionSuiteError):
            suite.run_suite(patch_payload=None)

if __name__ == "__main__":
    unittest.main()