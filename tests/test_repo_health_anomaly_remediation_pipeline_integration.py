import unittest
import uuid
import random
import os
import tempfile
from skills.repo_health_anomaly_remediation_pipeline import repo_health_anomaly_remediation_pipeline

class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.anomaly_id = str(uuid.uuid4())
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.target_metric = f"metric_{uuid.uuid4().hex[:8]}"

        self.input_payload = {
            "repo_path": self.repo_path,
            "anomaly_id": self.anomaly_id,
            "severity": self.severity_level,
            "metric": self.target_metric,
            "random_seed": random.randint(1, 10000)
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_remediation_pipeline_integration(self):
        result = repo_health_anomaly_remediation_pipeline(self.input_payload)

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result.get("anomaly_id"), self.anomaly_id)

        if result.get("status") == "SUCCESS":
            self.assertTrue(
                os.path.exists(os.path.join(self.repo_path, "remediation_report.json")) or
                result.get("remediated") is True
            )

        self.assertIn("execution_trace", result)
        self.assertIsInstance(result["execution_trace"], list)
        self.assertTrue(len(result["execution_trace"]) > 0)

if __name__ == "__main__":
    unittest.main()