import unittest
import uuid
import tempfile
import os
import shutil
from skills.repo_health_anomaly_remediation_pipeline import (
    RepoHealthAnomalyRemediationPipeline,
    run_remediation_pipeline,
    inspect_anomalies,
    RemediationExecutionError
)

class RealInspector:
    def inspect_repository(self, repo_path):
        payload = {"target_path": repo_path}
        res = inspect_anomalies(payload)
        if res.get("anomaly_detected"):
            return {"anomaly_id": str(uuid.uuid4())}
        return None

class RealAutomator:
    def execute_remediation(self, repo_path, anomaly):
        run_id = anomaly.get("anomaly_id")
        payload = {"run_id": run_id, "target_path": repo_path}
        run_remediation_pipeline(payload)
        return {"token": str(uuid.uuid4())}

class RealRestorer:
    def restore_state(self, repo_path, anomaly_id):
        marker = os.path.join(repo_path, f".remediated_{anomaly_id}")
        if os.path.exists(marker):
            os.remove(marker)

class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pipeline_id = str(uuid.uuid4())
        self.inspector = RealInspector()
        self.automator = RealAutomator()
        self.restorer = RealRestorer()
        self.pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=self.inspector,
            automator=self.automator,
            restorer=self.restorer
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_end_to_end_remediation_flow(self):
        result_first = self.pipeline.run_pipeline(self.test_dir)
        self.assertEqual(result_first["pipeline_id"], self.pipeline_id)
        self.assertEqual(result_first["status"], "remediated")
        self.assertIn("token", result_first)
        
        anomaly_id = result_first["anomaly_id"]
        expected_marker = os.path.join(self.test_dir, f".remediated_{anomaly_id}")
        self.assertTrue(os.path.exists(expected_marker), "Реальный файл маркера ремедиации должен быть создан на диске")

        result_second = self.pipeline.run_pipeline(self.test_dir)
        self.assertEqual(result_second["status"], "healthy")
        self.assertFalse(result_second["remediated"])

    def test_batch_remediate_integration(self):
        dir_one = tempfile.mkdtemp()
        dir_two = tempfile.mkdtemp()
        try:
            reports = self.pipeline.batch_remediate([dir_one, dir_two])
            self.assertEqual(len(reports), 2)
            for report in reports:
                self.assertEqual(report["status"], "remediated")
                self.assertTrue(os.path.exists(os.path.join(report["repo_path"], f".remediated_{report['anomaly_id']}")))
        finally:
            shutil.rmtree(dir_one)
            shutil.rmtree(dir_two)

if __name__ == "__main__":
    unittest.main()