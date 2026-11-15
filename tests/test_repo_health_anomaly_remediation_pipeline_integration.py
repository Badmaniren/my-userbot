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
            return {"anomaly_id": f"anomaly-{uuid.uuid4()}"}
        return None

class RealAutomator:
    def execute_remediation(self, repo_path, anomaly):
        run_id = str(uuid.uuid4())
        payload = {
            "run_id": run_id,
            "target_path": repo_path
        }
        run_remediation_pipeline(payload)
        return {"token": f"token-{uuid.uuid4()}"}

class RealRestorer:
    def restore_state(self, repo_path, anomaly_id):
        marker_files = [f for f in os.listdir(repo_path) if f.startswith(".remediated_")]
        for mf in marker_files:
            os.remove(os.path.join(repo_path, mf))

class RealLogger:
    def __init__(self):
        self.logs = []
    def log(self, message):
        self.logs.append(message)


class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.pipeline_id = f"pipe-{uuid.uuid4()}"
        
        self.inspector = RealInspector()
        self.automator = RealAutomator()
        self.restorer = RealRestorer()
        self.logger = RealLogger()
        
        self.pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=self.inspector,
            automator=self.automator,
            restorer=self.restorer,
            logger=self.logger
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_full_remediation_flow(self):
        result = self.pipeline.run_pipeline(self.repo_path)
        
        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("repo_path"), self.repo_path)
        self.assertEqual(result.get("status"), "remediated")
        self.assertIsNotNone(result.get("token"))
        self.assertIsNotNone(result.get("anomaly_id"))
        
        files = os.listdir(self.repo_path)
        remediated_files = [f for f in files if f.startswith(".remediated_")]
        self.assertTrue(len(remediated_files) > 0)
        
        second_result = self.pipeline.run_pipeline(self.repo_path)
        self.assertEqual(second_result.get("status"), "healthy")
        self.assertFalse(second_result.get("remediated"))

    def test_integration_analyze_anomaly_stream(self):
        log_file_path = os.path.join(self.repo_path, f"stream_{uuid.uuid4()}.log")
        random_content = "".join([chr(random.randint(65, 90)) for _ in range(random.randint(5, 50))])
        with open(log_file_path, "w") as f:
            f.write(random_content)
            
        metric_name = f"metric-{uuid.uuid4()}"
        threshold = float(random.randint(10, 100))
        
        stream_res = self.pipeline.analyze_anomaly_stream(log_file_path, metric_name, threshold)
        
        self.assertTrue(stream_res.get("stream_processed"))
        self.assertEqual(stream_res.get("metric"), metric_name)
        self.assertIn("anomaly_score", stream_res)
        self.assertIsInstance(stream_res.get("anomaly_score"), float)

    def test_integration_batch_remediate(self):
        repo_paths = []
        for _ in range(3):
            sub_dir = tempfile.TemporaryDirectory(dir=self.repo_path)
            repo_paths.append(sub_dir.name)
            
        reports = self.pipeline.batch_remediate(repo_paths)
        self.assertEqual(len(reports), 3)
        for r in reports:
            self.assertEqual(r.get("status"), "remediated")
            
        for path in repo_paths:
            files = os.listdir(path)
            self.assertTrue(any(f.startswith(".remediated_") for f in files))

if __name__ == "__main__":
    unittest.main()