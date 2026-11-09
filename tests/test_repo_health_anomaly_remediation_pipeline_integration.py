import unittest
import os
import tempfile
import uuid
import random
from skills.repo_health_anomaly_remediation_pipeline import (
    RepoHealthAnomalyRemediationPipeline,
    RemediationExecutionError,
    run_remediation_pipeline,
    inspect_anomalies
)

class RealInspector:
    def inspect_repository(self, repo_path):
        payload = {"target_path": repo_path}
        res = inspect_anomalies(payload)
        if res.get("anomaly_detected"):
            return {"anomaly_id": f"anomaly_{uuid.uuid4()}"}
        return None

class RealAutomator:
    def execute_remediation(self, repo_path, anomaly):
        run_id = str(uuid.uuid4())
        payload = {"run_id": run_id, "target_path": repo_path}
        run_remediation_pipeline(payload)
        return {"token": f"token_{uuid.uuid4()}"}

class RealRestorer:
    def __init__(self):
        self.restored_calls = []

    def restore_state(self, repo_path, anomaly_id):
        self.restored_calls.append((repo_path, anomaly_id))
        marker_files = [f for f in os.listdir(repo_path) if f.startswith(".remediated_")]
        for mf in marker_files:
            os.remove(os.path.join(repo_path, mf))

class RealFailingAutomator:
    def execute_remediation(self, repo_path, anomaly):
        raise ValueError(f"Failed remediation for {anomaly.get('anomaly_id')}")

class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.pipeline_id = f"pipe_{uuid.uuid4()}"

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
        self.test_dir.cleanup()

    def test_pipeline_healthy_repository(self):
        run_id = str(uuid.uuid4())
        payload = {"run_id": run_id, "target_path": self.repo_path}
        run_remediation_pipeline(payload)

        result = self.pipeline.run_pipeline(self.repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["remediated"])

    def test_pipeline_anomaly_remediation_success(self):
        result = self.pipeline.run_pipeline(self.repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "remediated")
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertIn("anomaly_", result["anomaly_id"])
        self.assertIn("token_", result["token"])
        
        files = os.listdir(self.repo_path)
        markers = [f for f in files if f.startswith(".remediated_")]
        self.assertTrue(len(markers) > 0)

    def test_pipeline_remediation_failure_and_rollback(self):
        failing_pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=self.inspector,
            automator=RealFailingAutomator(),
            restorer=self.restorer
        )

        with self.assertRaises(RemediationExecutionError):
            failing_pipeline.run_pipeline(self.repo_path)

        self.assertEqual(len(self.restorer.restored_calls), 1)

    def test_analyze_anomaly_stream_integration(self):
        log_file_path = os.path.join(self.repo_path, f"log_{uuid.uuid4()}.txt")
        random_content = "".join(random.choices("ABCDEF0123456789\n", k=random.randint(50, 200)))
        with open(log_file_path, "w") as f:
            f.write(random_content)

        metric_name = f"metric_{uuid.uuid4()}"
        threshold = random.uniform(10.0, 100.0)

        analysis = self.pipeline.analyze_anomaly_stream(log_file_path, metric_name, threshold)

        self.assertTrue(analysis["stream_processed"])
        self.assertEqual(analysis["metric"], metric_name)
        self.assertIsInstance(analysis["anomaly_score"], float)

    def test_batch_remediate_integration(self):
        temp_dirs = [tempfile.TemporaryDirectory() for _ in range(3)]
        repo_paths = [d.name for d in temp_dirs]

        try:
            reports = self.pipeline.batch_remediate(repo_paths)
            self.assertEqual(len(reports), 3)
            for r in reports:
                self.assertEqual(r["status"], "remediated")
        finally:
            for d in temp_dirs:
                d.cleanup()

if __name__ == "__main__":
    unittest.main()