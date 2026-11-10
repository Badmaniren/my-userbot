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
    def __init__(self, anomaly_id):
        self.anomaly_id = anomaly_id

    def inspect_repository(self, repo_path):
        marker = os.path.join(repo_path, ".anomaly_marker")
        if os.path.exists(marker):
            return {"anomaly_id": self.anomaly_id, "severity": "HIGH"}
        return None


class RealAutomator:
    def __init__(self, token):
        self.token = token

    def execute_remediation(self, repo_path, anomaly):
        marker = os.path.join(repo_path, ".anomaly_marker")
        if os.path.exists(marker):
            os.remove(marker)
        fix_file = os.path.join(repo_path, f"fixed_{anomaly.get('anomaly_id')}.txt")
        with open(fix_file, "w") as f:
            f.write("resolved")
        return {"token": self.token}


class FailingAutomator:
    def execute_remediation(self, repo_path, anomaly):
        raise ValueError("Critical remediation failure")


class RealRestorer:
    def __init__(self):
        self.restored_calls = []

    def restore_state(self, repo_path, anomaly_id):
        self.restored_calls.append((repo_path, anomaly_id))
        marker = os.path.join(repo_path, ".anomaly_marker")
        with open(marker, "w") as f:
            f.write("restored")


class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pipeline_id = str(uuid.uuid4())
        self.anomaly_id = str(uuid.uuid4())
        self.token = str(uuid.uuid4())

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_pipeline_healthy_repository(self):
        inspector = RealInspector(self.anomaly_id)
        automator = RealAutomator(self.token)
        restorer = RealRestorer()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        result = pipeline.run_pipeline(self.test_dir)

        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("status"), "healthy")
        self.assertFalse(result.get("remediated"))

    def test_pipeline_remediation_success(self):
        marker = os.path.join(self.test_dir, ".anomaly_marker")
        with open(marker, "w") as f:
            f.write("anomaly")

        inspector = RealInspector(self.anomaly_id)
        automator = RealAutomator(self.token)
        restorer = RealRestorer()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        result = pipeline.run_pipeline(self.test_dir)

        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("repo_path"), self.test_dir)
        self.assertEqual(result.get("anomaly_id"), self.anomaly_id)
        self.assertEqual(result.get("status"), "remediated")
        self.assertEqual(result.get("token"), self.token)

        fix_file = os.path.join(self.test_dir, f"fixed_{self.anomaly_id}.txt")
        self.assertTrue(os.path.exists(fix_file))
        self.assertFalse(os.path.exists(marker))

    def test_pipeline_remediation_failure_and_restoration(self):
        marker = os.path.join(self.test_dir, ".anomaly_marker")
        with open(marker, "w") as f:
            f.write("anomaly")

        inspector = RealInspector(self.anomaly_id)
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
        self.assertEqual(restorer.restored_calls[0], (self.test_dir, self.anomaly_id))
        self.assertTrue(os.path.exists(marker))

    def test_analyze_anomaly_stream_integration(self):
        log_file = os.path.join(self.test_dir, f"stream_{uuid.uuid4()}.log")
        random_content = "".join(random.choices("ABCDEF0123456789\n", k=random.randint(50, 200)))
        with open(log_file, "w") as f:
            f.write(random_content)

        pipeline = RepoHealthAnomalyRemediationPipeline(pipeline_id=self.pipeline_id)
        metric_name = f"metric_{uuid.uuid4()}"
        threshold = float(random.randint(10, 100))

        analysis = pipeline.analyze_anomaly_stream(log_file, metric_name, threshold)

        self.assertTrue(analysis.get("stream_processed"))
        self.assertEqual(analysis.get("metric"), metric_name)
        self.assertIn("anomaly_score", analysis)
        self.assertIsInstance(analysis.get("anomaly_score"), float)

    def test_batch_remediate_integration(self):
        dir_count = random.randint(2, 4)
        paths = []
        inspectors = []
        automators = []

        for _ in range(dir_count):
            d = tempfile.mkdtemp(dir=self.test_dir)
            paths.append(d)
            m = os.path.join(d, ".anomaly_marker")
            with open(m, "w") as f:
                f.write("anomaly")

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=RealInspector(self.anomaly_id),
            automator=RealAutomator(self.token),
            restorer=RealRestorer()
        )

        reports = pipeline.batch_remediate(paths)
        self.assertEqual(len(reports), dir_count)
        for rep in reports:
            self.assertEqual(rep.get("status"), "remediated")
            self.assertEqual(rep.get("token"), self.token)

    def test_functional_helpers_integration(self):
        run_id = str(uuid.uuid4())
        payload = {
            "run_id": run_id,
            "target_path": self.test_dir
        }

        inspection_before = inspect_anomalies(payload)
        self.assertTrue(inspection_before.get("anomaly_detected"))

        res = run_remediation_pipeline(payload)
        self.assertEqual(res.get("run_id"), run_id)
        self.assertEqual(res.get("status"), "remediated")

        inspection_after = inspect_anomalies(payload)
        self.assertFalse(inspection_after.get("anomaly_detected"))


if __name__ == "__main__":
    unittest.main()