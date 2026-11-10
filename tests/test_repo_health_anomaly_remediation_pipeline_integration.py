import unittest
import os
import shutil
import uuid
import random

from skills.repo_health_anomaly_remediation_pipeline import (
    RepoHealthAnomalyRemediationPipeline,
    RemediationExecutionError,
    run_remediation_pipeline,
    inspect_anomalies
)

class RealInspector:
    def __init__(self, should_detect=True, anomaly_id=None):
        self.should_detect = should_detect
        self.anomaly_id = anomaly_id or str(uuid.uuid4())

    def inspect_repository(self, repo_path):
        if not self.should_detect:
            return None
        return {
            "anomaly_id": self.anomaly_id,
            "severity": "HIGH"
        }

class RealAutomator:
    def __init__(self, fail=False):
        self.fail = fail

    def execute_remediation(self, repo_path, anomaly):
        if self.fail:
            raise RuntimeError("Remediation execution crashed intentionally")
        token = str(uuid.uuid4())
        marker_file = os.path.join(repo_path, f".remediated_{token}")
        with open(marker_file, "w") as f:
            f.write(anomaly.get("anomaly_id", "unknown"))
        return {"token": token}

class RealRestorer:
    def __init__(self):
        self.restored_calls = []

    def restore_state(self, repo_path, anomaly_id):
        self.restored_calls.append((repo_path, anomaly_id))
        marker_file = os.path.join(repo_path, f".restored_{anomaly_id}")
        with open(marker_file, "w") as f:
            f.write("restored")

class RealLogger:
    def __init__(self):
        self.logs = []

    def log(self, message):
        self.logs.append(message)


class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.join(os.getcwd(), f"test_repo_{uuid.uuid4().hex}")
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_integration_successful_remediation(self):
        pipeline_id = str(uuid.uuid4())
        expected_anomaly_id = str(uuid.uuid4())

        inspector = RealInspector(should_detect=True, anomaly_id=expected_anomaly_id)
        automator = RealAutomator(fail=False)
        restorer = RealRestorer()
        logger = RealLogger()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer,
            logger=logger
        )

        result = pipeline.run_pipeline(self.test_dir)

        self.assertEqual(result.get("pipeline_id"), pipeline_id)
        self.assertEqual(result.get("repo_path"), self.test_dir)
        self.assertEqual(result.get("anomaly_id"), expected_anomaly_id)
        self.assertEqual(result.get("status"), "remediated")
        
        token = result.get("token")
        self.assertIsNotNone(token)

        marker_path = os.path.join(self.test_dir, f".remediated_{token}")
        self.assertTrue(os.path.exists(marker_path))

    def test_integration_failure_and_restoration(self):
        pipeline_id = str(uuid.uuid4())
        expected_anomaly_id = str(uuid.uuid4())

        inspector = RealInspector(should_detect=True, anomaly_id=expected_anomaly_id)
        automator = RealAutomator(fail=True)
        restorer = RealRestorer()
        logger = RealLogger()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer,
            logger=logger
        )

        with self.assertRaises(RemediationExecutionError):
            pipeline.run_pipeline(self.test_dir)

        self.assertEqual(len(restorer.restored_calls), 1)
        self.assertEqual(restorer.restored_calls[0], (self.test_dir, expected_anomaly_id))

        restored_marker = os.path.join(self.test_dir, f".restored_{expected_anomaly_id}")
        self.assertTrue(os.path.exists(restored_marker))

    def test_integration_healthy_repository(self):
        pipeline_id = str(uuid.uuid4())
        inspector = RealInspector(should_detect=False)
        automator = RealAutomator(fail=False)
        restorer = RealRestorer()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        result = pipeline.run_pipeline(self.test_dir)

        self.assertEqual(result.get("pipeline_id"), pipeline_id)
        self.assertEqual(result.get("status"), "healthy")
        self.assertFalse(result.get("remediated"))
        self.assertEqual(len(restorer.restored_calls), 0)

    def test_integration_batch_remediate(self):
        dir_count = random.randint(2, 4)
        repo_paths = []
        for _ in range(dir_count):
            d = os.path.join(self.test_dir, f"sub_repo_{uuid.uuid4().hex}")
            os.makedirs(d, exist_ok=True)
            repo_paths.append(d)

        inspector = RealInspector(should_detect=True)
        automator = RealAutomator(fail=False)
        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=str(uuid.uuid4()),
            inspector=inspector,
            automator=automator
        )

        reports = pipeline.batch_remediate(repo_paths)
        self.assertEqual(len(reports), dir_count)
        for report in reports:
            self.assertEqual(report.get("status"), "remediated")
            self.assertIsNotNone(report.get("token"))

    def test_integration_standalone_functions(self):
        run_id = str(uuid.uuid4().hex[:8])
        target_path = os.path.join(self.test_dir, f"target_{uuid.uuid4().hex}")
        
        payload = {
            "run_id": run_id,
            "target_path": target_path
        }

        rem_res = run_remediation_pipeline(payload)
        self.assertEqual(rem_res.get("run_id"), run_id)
        self.assertEqual(rem_res.get("status"), "remediated")

        marker = os.path.join(target_path, f".remediated_{run_id}")
        self.assertTrue(os.path.exists(marker))

        inspection_res = inspect_anomalies(payload)
        self.assertFalse(inspection_res.get("anomaly_detected"))


if __name__ == "__main__":
    unittest.main()