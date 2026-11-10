import unittest
import os
import tempfile
import shutil
import uuid
import random

from skills.repo_health_anomaly_remediation_pipeline import (
    RepoHealthAnomalyRemediationPipeline,
    RemediationExecutionError,
    AnomalySeverity
)

class RealInspector:
    def inspect_repository(self, repo_path):
        marker_path = os.path.join(repo_path, "anomaly.flag")
        if os.path.exists(marker_path):
            with open(marker_path, "r") as f:
                anomaly_id = f.read().strip()
            return {"anomaly_id": anomaly_id, "severity": AnomalySeverity.HIGH.name}
        return None

class RealAutomator:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    def execute_remediation(self, repo_path, anomaly):
        if self.should_fail:
            raise RuntimeError("Remediation execution crashed explicitly.")
        token = f"token_{uuid.uuid4().hex}"
        fixed_file = os.path.join(repo_path, "fixed.txt")
        with open(fixed_file, "w") as f:
            f.write(token)
        return {"token": token}

class RealRestorer:
    def __init__(self):
        self.restored_calls = []

    def restore_state(self, repo_path, anomaly_id):
        self.restored_calls.append((repo_path, anomaly_id))
        restored_file = os.path.join(repo_path, "restored.flag")
        with open(restored_file, "w") as f:
            f.write(str(anomaly_id))

class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pipeline_id = f"pipe_{uuid.uuid4().hex[:8]}"

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_pipeline_healthy_repository(self):
        inspector = RealInspector()
        automator = RealAutomator()
        restorer = RealRestorer()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        result = pipeline.run_pipeline(self.test_dir)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["remediated"])
        self.assertEqual(len(restorer.restored_calls), 0)

    def test_pipeline_anomaly_remediation_success(self):
        anomaly_id = f"anom_{random.randint(1000, 9999)}"
        marker_path = os.path.join(self.test_dir, "anomaly.flag")
        with open(marker_path, "w") as f:
            f.write(anomaly_id)

        inspector = RealInspector()
        automator = RealAutomator(should_fail=False)
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
        self.assertEqual(result["anomaly_id"], anomaly_id)
        self.assertIn("token_", result["token"])

        fixed_file = os.path.join(self.test_dir, "fixed.txt")
        self.assertTrue(os.path.exists(fixed_file))
        with open(fixed_file, "r") as f:
            content = f.read()
        self.assertEqual(content, result["token"])
        self.assertEqual(len(restorer.restored_calls), 0)

    def test_pipeline_anomaly_remediation_failure_with_restoration(self):
        anomaly_id = f"anom_{uuid.uuid4().hex[:6]}"
        marker_path = os.path.join(self.test_dir, "anomaly.flag")
        with open(marker_path, "w") as f:
            f.write(anomaly_id)

        inspector = RealInspector()
        automator = RealAutomator(should_fail=True)
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
        self.assertEqual(restorer.restored_calls[0], (self.test_dir, anomaly_id))

        restored_file = os.path.join(self.test_dir, "restored.flag")
        self.assertTrue(os.path.exists(restored_file))
        with open(restored_file, "r") as f:
            self.assertEqual(f.read().strip(), anomaly_id)

    def test_analyze_anomaly_stream_integration(self):
        log_file = os.path.join(self.test_dir, "audit.log")
        random_content = "".join(random.choices("ABCDEF0123456789\n", k=random.randint(50, 200)))
        with open(log_file, "w") as f:
            f.write(random_content)

        pipeline = RepoHealthAnomalyRemediationPipeline(pipeline_id=self.pipeline_id)
        metric_name = f"metric_{uuid.uuid4().hex[:4]}"
        threshold = float(random.randint(10, 100))

        result = pipeline.analyze_anomaly_stream(log_file, metric_name, threshold)

        self.assertTrue(result["stream_processed"])
        self.assertEqual(result["metric"], metric_name)
        self.assertIsInstance(result["anomaly_score"], float)
        self.assertGreaterEqual(result["anomaly_score"], 0.0)
        self.assertLessEqual(result["anomaly_score"], threshold)

    def test_batch_remediate_integration(self):
        sub_dirs = []
        for i in range(3):
            d = os.path.join(self.test_dir, f"repo_{i}_{uuid.uuid4().hex[:4]}")
            os.makedirs(d)
            if i % 2 == 0:
                with open(os.path.join(d, "anomaly.flag"), "w") as f:
                    f.write(f"batch_anom_{i}")
            sub_dirs.append(d)

        inspector = RealInspector()
        automator = RealAutomator(should_fail=False)
        restorer = RealRestorer()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        reports = pipeline.batch_remediate(sub_dirs)

        self.assertEqual(len(reports), 3)
        self.assertEqual(reports[0]["status"], "remediated")
        self.assertEqual(reports[1]["status"], "healthy")
        self.assertEqual(reports[2]["status"], "remediated")

if __name__ == "__main__":
    unittest.main()