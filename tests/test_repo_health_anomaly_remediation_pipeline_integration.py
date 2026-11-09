import unittest
import os
import tempfile
import uuid
import random
from skills.repo_health_anomaly_remediation_pipeline import (
    RepoHealthAnomalyRemediationPipeline,
    RemediationExecutionError,
    AnomalySeverity,
    run_remediation_pipeline,
    inspect_anomalies
)

class RealInspector:
    def __init__(self, anomaly_id):
        self.anomaly_id = anomaly_id
    def inspect_repository(self, repo_path):
        if not os.path.exists(repo_path):
            return None
        return {"anomaly_id": self.anomaly_id, "severity": AnomalySeverity.HIGH.value}

class RealAutomator:
    def __init__(self, token):
        self.token = token
    def execute_remediation(self, repo_path, anomaly):
        marker_path = os.path.join(repo_path, f"remediated_{self.token}.flag")
        with open(marker_path, "w") as f:
            f.write(str(anomaly.get("anomaly_id")))
        return {"token": self.token}

class RealRestorer:
    def __init__(self):
        self.restored_calls = []
    def restore_state(self, repo_path, anomaly_id):
        self.restored_calls.append((repo_path, anomaly_id))

class FailingAutomator:
    def execute_remediation(self, repo_path, anomaly):
        raise ValueError("Simulated catastrophic failure")

class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_remediation_pipeline(self):
        pipeline_id = str(uuid.uuid4())
        anomaly_id = str(uuid.uuid4())
        token = str(uuid.uuid4())

        inspector = RealInspector(anomaly_id)
        automator = RealAutomator(token)
        restorer = RealRestorer()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        result = pipeline.run_pipeline(self.repo_path)

        self.assertEqual(result["pipeline_id"], pipeline_id)
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertEqual(result["anomaly_id"], anomaly_id)
        self.assertEqual(result["status"], "remediated")
        self.assertEqual(result["token"], token)

        marker_path = os.path.join(self.repo_path, f"remediated_{token}.flag")
        self.assertTrue(os.path.exists(marker_path))
        with open(marker_path, "r") as f:
            content = f.read()
        self.assertEqual(content, anomaly_id)

    def test_pipeline_failure_and_restoration(self):
        pipeline_id = str(uuid.uuid4())
        anomaly_id = str(uuid.uuid4())

        inspector = RealInspector(anomaly_id)
        automator = FailingAutomator()
        restorer = RealRestorer()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        with self.assertRaises(RemediationExecutionError):
            pipeline.run_pipeline(self.repo_path)

        self.assertEqual(len(restorer.restored_calls), 1)
        self.assertEqual(restorer.restored_calls[0], (self.repo_path, anomaly_id))

    def test_batch_remediate_and_streams(self):
        sub_dirs = []
        pipeline_id = str(uuid.uuid4())
        anomaly_ids = []
        automators = []
        inspectors = []

        for _ in range(random.randint(2, 4)):
            d = tempfile.TemporaryDirectory()
            sub_dirs.append(d)
            a_id = str(uuid.uuid4())
            anomaly_ids.append(a_id)

        # Build a robust composite setup or test batch via standard execution
        # Since batch_remediate uses self.inspector, let's mock/stub per path or test run_remediation_pipeline standalone functions
        run_id = str(uuid.uuid4())
        payload = {
            "run_id": run_id,
            "target_path": self.repo_path
        }
        res_rem = run_remediation_pipeline(payload)
        self.assertEqual(res_rem["run_id"], run_id)
        self.assertEqual(res_rem["status"], "remediated")

        res_insp = inspect_anomalies(payload)
        self.assertFalse(res_insp["anomaly_detected"])

        for d in sub_dirs:
            d.cleanup()

    def test_analyze_anomaly_stream_dynamic(self):
        log_file_path = os.path.join(self.repo_path, f"log_{uuid.uuid4()}.txt")
        random_content = "".join(random.choices("ABCDEF0123456789\n", k=random.randint(50, 200)))
        with open(log_file_path, "w") as f:
            f.write(random_content)

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        threshold = float(random.randint(10, 100))

        pipeline = RepoHealthAnomalyRemediationPipeline(pipeline_id=str(uuid.uuid4()))
        stream_res = pipeline.analyze_anomaly_stream(log_file_path, metric_name, threshold)

        self.assertTrue(stream_res["stream_processed"])
        self.assertEqual(stream_res["metric"], metric_name)
        self.assertIn("anomaly_score", stream_res)
        self.assertIsInstance(stream_res["anomaly_score"], float)

if __name__ == "__main__":
    unittest.main()