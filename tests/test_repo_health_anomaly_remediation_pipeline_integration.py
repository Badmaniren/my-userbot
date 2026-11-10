import unittest
import os
import tempfile
import uuid
import random
from skills.repo_health_anomaly_remediation_pipeline import (
    RepoHealthAnomalyRemediationPipeline,
    AnomalySeverity,
    RemediationExecutionError,
    run_remediation_pipeline,
    inspect_anomalies
)

class RealInspectorStub:
    def __init__(self, anomaly_dict):
        self.anomaly_dict = anomaly_dict
    def inspect_repository(self, repo_path):
        return self.anomaly_dict

class RealAutomatorStub:
    def __init__(self, token):
        self.token = token
    def execute_remediation(self, repo_path, anomaly):
        return {"token": self.token}

class RealRestorerStub:
    def __init__(self):
        self.restored = False
    def restore_state(self, repo_path, anomaly_id):
        self.restored = True

class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.pipeline_id = str(uuid.uuid4())
        self.anomaly_id = f"anomaly_{uuid.uuid4().hex[:8]}"
        self.token = f"token_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_run_pipeline_end_to_end_remediated(self):
        anomaly_data = {
            "anomaly_id": self.anomaly_id,
            "severity": random.choice(list(AnomalySeverity)).name
        }
        inspector = RealInspectorStub(anomaly_data)
        automator = RealAutomatorStub(self.token)
        restorer = RealRestorerStub()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        result = pipeline.run_pipeline(self.repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertEqual(result["anomaly_id"], self.anomaly_id)
        self.assertEqual(result["status"], "remediated")
        self.assertEqual(result["token"], self.token)
        self.assertFalse(restorer.restored)

    def test_run_pipeline_healthy(self):
        inspector = RealInspectorStub(None)
        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=inspector
        )

        result = pipeline.run_pipeline(self.repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["remediated"])

    def test_run_pipeline_failure_and_restore(self):
        class FailingAutomator:
            def execute_remediation(self, repo_path, anomaly):
                raise RuntimeError("Remediation execution crashed.")

        anomaly_data = {
            "anomaly_id": self.anomaly_id,
            "severity": "CRITICAL"
        }
        inspector = RealInspectorStub(anomaly_data)
        automator = FailingAutomator()
        restorer = RealRestorerStub()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        with self.assertRaises(RemediationExecutionError):
            pipeline.run_pipeline(self.repo_path)

        self.assertTrue(restorer.restored)

    def test_analyze_anomaly_stream_integration(self):
        log_file_path = os.path.join(self.repo_path, f"stream_{uuid.uuid4().hex}.log")
        random_content = "".join(random.choices("ABCDEF0123456789", k=random.randint(10, 50)))
        with open(log_file_path, "w") as f:
            f.write(random_content)

        pipeline = RepoHealthAnomalyRemediationPipeline(pipeline_id=self.pipeline_id)
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        threshold = float(random.randint(5, 100))

        res = pipeline.analyze_anomaly_stream(log_file_path, metric_name, threshold)

        self.assertTrue(res["stream_processed"])
        self.assertEqual(res["metric"], metric_name)
        self.assertIsInstance(res["anomaly_score"], float)

    def test_batch_remediate_integration(self):
        path1 = tempfile.mkdtemp(dir=self.repo_path)
        path2 = tempfile.mkdtemp(dir=self.repo_path)
        paths = [path1, path2]

        inspector = RealInspectorStub(None)
        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=inspector
        )

        reports = pipeline.batch_remediate(paths)
        self.assertEqual(len(reports), 2)
        for rep in reports:
            self.assertEqual(rep["status"], "healthy")

    def test_helper_functions_integration(self):
        run_id = str(uuid.uuid4())
        payload = {
            "run_id": run_id,
            "target_path": self.repo_path
        }

        rem_res = run_remediation_pipeline(payload)
        self.assertEqual(rem_res["run_id"], run_id)
        self.assertEqual(rem_res["status"], "remediated")

        marker_files = os.listdir(self.repo_path)
        self.assertTrue(any(f.startswith(f".remediated_{run_id}") for f in marker_files))

        inspection_res = inspect_anomalies(payload)
        self.assertFalse(inspection_res["anomaly_detected"])

if __name__ == "__main__":
    unittest.main()