import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.repo_health_anomaly_remediation_pipeline import (
    RepoHealthAnomalyRemediationPipeline,
    RemediationExecutionError,
    run_remediation_pipeline,
    inspect_anomalies
)

class RealInspector:
    def inspect_repository(self, repo_path):
        files = os.listdir(repo_path)
        has_marker = any(f.startswith(".remediated_") for f in files)
        if has_marker:
            return None
        return {"anomaly_id": f"anomaly-{uuid.uuid4()}", "severity": "HIGH"}

class RealAutomator:
    def __init__(self, token):
        self.token = token
    def execute_remediation(self, repo_path, anomaly):
        marker_path = os.path.join(repo_path, f".remediated_{uuid.uuid4()}")
        with open(marker_path, "w") as f:
            f.write("fixed")
        return {"token": self.token}

class FailingAutomator:
    def execute_remediation(self, repo_path, anomaly):
        raise ValueError("Critical automation failure")

class RealRestorer:
    def __init__(self):
        self.restored_calls = []
    def restore_state(self, repo_path, anomaly_id):
        self.restored_calls.append((repo_path, anomaly_id))
        marker_path = os.path.join(repo_path, f"restored_{anomaly_id}")
        with open(marker_path, "w") as f:
            f.write("restored")

class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pipeline_id = str(uuid.uuid4())
        self.expected_token = str(uuid.uuid4())

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_integration_successful_remediation_flow(self):
        inspector = RealInspector()
        automator = RealAutomator(self.expected_token)
        restorer = RealRestorer()
        
        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        result = pipeline.run_pipeline(self.test_dir)
        
        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "remediated")
        self.assertEqual(result["token"], self.expected_token)
        self.assertTrue(result["anomaly_id"].startswith("anomaly-"))
        
        files = os.listdir(self.test_dir)
        remediated_files = [f for f in files if f.startswith(".remediated_")]
        self.assertEqual(len(remediated_files), 1)

    def test_integration_failure_and_restoration_flow(self):
        inspector = RealInspector()
        automator = FailingAutomator()
        restorer = RealRestorer()
        
        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        with self.assertRaises(RemediationExecutionError):
            pipeline.run_pipeline(self.test_dir)

        self.assertEqual(len(restorer.restored_calls), 1)
        restored_path, anomaly_id = restorer.restored_calls[0]
        self.assertEqual(restored_path, self.test_dir)
        
        files = os.listdir(self.test_dir)
        restored_files = [f for f in files if f.startswith("restored_")]
        self.assertEqual(len(restored_files), 1)

    def test_integration_batch_and_standalone_functions(self):
        run_id = str(uuid.uuid4())
        payload = {
            "run_id": run_id,
            "target_path": self.test_dir
        }
        
        rem_res = run_remediation_pipeline(payload)
        self.assertEqual(rem_res["run_id"], run_id)
        self.assertEqual(rem_res["status"], "remediated")

        insp_res = inspect_anomalies(payload)
        self.assertFalse(insp_res["anomaly_id"] if "anomaly_id" in insp_res else insp_res.get("anomaly_detected", True))

        metric_name = f"metric-{uuid.uuid4()}"
        threshold = random.uniform(10.0, 100.0)
        
        log_file = os.path.join(self.test_dir, "test.log")
        random_content = "".join(random.choices("ABCDEF0123456789", k=random.randint(50, 200)))
        with open(log_file, "w") as f:
            f.write(random_content)

        pipeline = RepoHealthAnomalyRemediationPipeline(pipeline_id=self.pipeline_id)
        stream_res = pipeline.analyze_anomaly_stream(log_file, metric_name, threshold)
        
        self.assertTrue(stream_res["stream_processed"])
        self.assertEqual(stream_res["metric"], metric_name)
        self.assertIsInstance(stream_res["anomaly_score"], float)

        sub_dir_1 = tempfile.mkdtemp(dir=self.test_dir)
        sub_dir_2 = tempfile.mkdtemp(dir=self.test_dir)
        
        batch_pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=RealInspector(),
            automator=RealAutomator(self.expected_token)
        )
        
        reports = batch_pipeline.batch_remediate([sub_dir_1, sub_dir_2])
        self.assertEqual(len(reports), 2)
        for rep in reports:
            self.assertEqual(rep["status"], "remediated")

if __name__ == "__main__":
    unittest.main()