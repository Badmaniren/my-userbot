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
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector
from skills.repo_health_automator import RepoHealthAutomator
from skills.repo_health_restorer import RepoHealthRestorer
from skills.repo_logger import RepoLogger


class RealInspector:
    def inspect_repository(self, repo_path):
        payload = {"target_path": repo_path}
        res = inspect_anomalies(payload)
        if res.get("anomaly_detected"):
            return {"anomaly_id": f"anomaly_{uuid.uuid4().hex[:8]}"}
        return None


class RealAutomator:
    def execute_remediation(self, repo_path, anomaly):
        run_id = uuid.uuid4().hex[:8]
        payload = {"run_id": run_id, "target_path": repo_path}
        run_remediation_pipeline(payload)
        return {"token": f"token_{run_id}"}


class RealRestorer:
    def restore_state(self, repo_path, anomaly_id):
        marker_path = os.path.join(repo_path, f"restored_{anomaly_id}")
        with open(marker_path, "w") as f:
            f.write("restored")


class FailingAutomator:
    def execute_remediation(self, repo_path, anomaly):
        raise RuntimeError("Critical remediation failure")


class IntegrationRepoHealthAnomalyRemediationPipelineTest(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.pipeline_id = f"pipeline_{uuid.uuid4().hex[:6]}"
        
        self.inspector = RealInspector()
        self.automator = RealAutomator()
        self.restorer = RealRestorer()
        self.logger = RepoLogger()

        self.pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=self.inspector,
            automator=self.automator,
            restorer=self.restorer,
            logger=self.logger
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_pipeline_healthy_repository(self):
        for filename in os.listdir(self.repo_path):
            file_path = os.path.join(self.repo_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

        result = self.pipeline.run_pipeline(self.repo_path)
        
        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("status"), "healthy")
        self.assertFalse(result.get("remediated"))

    def test_integration_pipeline_remediation_success(self):
        anomaly_file = os.path.join(self.repo_path, f"artifact_{uuid.uuid4().hex[:4]}.txt")
        with open(anomaly_file, "w") as f:
            f.write("anomaly payload")

        result = self.pipeline.run_pipeline(self.repo_path)

        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("status"), "remediated")
        self.assertEqual(result.get("repo_path"), self.repo_path)
        self.assertIsNotNone(result.get("anomaly_id"))
        self.assertIsNotNone(result.get("token"))
        self.assertTrue(result.get("token").startswith("token_"))

        files = os.listdir(self.repo_path)
        markers = [f for f in files if f.startswith(".remediated_")]
        self.assertTrue(len(markers) > 0)

    def test_integration_pipeline_remediation_failure_and_restore(self):
        anomaly_file = os.path.join(self.repo_path, f"error_{uuid.uuid4().hex[:4]}.dat")
        with open(anomaly_file, "w") as f:
            f.write("error payload")

        failing_pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=self.inspector,
            automator=FailingAutomator(),
            restorer=self.restorer,
            logger=self.logger
        )

        with self.assertRaises(RemediationExecutionError):
            failing_pipeline.run_pipeline(self.repo_path)

        files = os.listdir(self.repo_path)
        restored_markers = [f for f in files if f.startswith("restored_")]
        self.assertTrue(len(restored_markers) > 0)

    def test_integration_analyze_anomaly_stream(self):
        log_file_path = os.path.join(self.repo_path, f"stream_{uuid.uuid4().hex[:4]}.log")
        random_content = "".join(random.choices("ABCDEF0123456789\n", k=random.randint(50, 150)))
        with open(log_file_path, "w") as f:
            f.write(random_content)

        metric_name = f"metric_{uuid.uuid4().hex[:4]}"
        threshold = random.uniform(10.0, 100.0)

        stream_result = self.pipeline.analyze_anomaly_stream(log_file_path, metric_name, threshold)

        self.assertTrue(stream_result.get("stream_processed"))
        self.assertEqual(stream_result.get("metric"), metric_name)
        self.assertIn("anomaly_score", stream_result)
        self.assertIsInstance(stream_result.get("anomaly_score"), float)

    def test_integration_batch_remediate(self):
        repo_paths = []
        for _ in range(random.randint(2, 4)):
            sub_dir = tempfile.mkdtemp(dir=self.repo_path)
            with open(os.path.join(sub_dir, f"anomaly_{uuid.uuid4().hex[:4]}.tmp"), "w") as f:
                f.write("data")
            repo_paths.append(sub_dir)

        reports = self.pipeline.batch_remediate(repo_paths)

        self.assertEqual(len(reports), len(repo_paths))
        for report in reports:
            self.assertEqual(report.get("status"), "remediated")
            self.assertIn("token", report)


if __name__ == "__main__":
    unittest.main()