import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.repo_health_anomaly_remediation_pipeline import run_remediation_pipeline
from skills.repo_health_anomaly_inspector import inspect_anomalies
from skills.repo_health_restorer import restore_repository
from skills.repo_logger import log_event

class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.run_id = str(uuid.uuid4())
        self.anomaly_score = round(random.uniform(0.5, 1.0), 4)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_remediation_pipeline_integration(self):
        payload = {
            "run_id": self.run_id,
            "target_path": self.test_dir,
            "anomaly_threshold": self.anomaly_score,
            "simulate_issue": True
        }

        result = run_remediation_pipeline(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("run_id"), self.run_id)
        self.assertIn("status", result)
        self.assertEqual(result.get("status"), "remediated")

        inspection = inspect_anomalies({"target_path": self.test_dir})
        self.assertIsInstance(inspection, dict)
        self.assertIn("anomaly_detected", inspection)
        self.assertFalse(inspection.get("anomaly_detected"))

        remediation_marker = os.path.join(self.test_dir, f".remediated_{self.run_id}")
        self.assertTrue(os.path.exists(remediation_marker))

if __name__ == "__main__":
    unittest.main()