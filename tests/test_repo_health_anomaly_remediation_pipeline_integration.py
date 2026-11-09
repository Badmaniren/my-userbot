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
    def __init__(self, expected_anomaly_id):
        self.expected_anomaly_id = expected_anomaly_id

    def inspect_repository(self, repo_path):
        payload = {"target_path": repo_path}
        res = inspect_anomalies(payload)
        if res.get("anomaly_detected"):
            return {"anomaly_id": self.expected_anomaly_id, "details": "Real anomaly found"}
        return None


class RealAutomator:
    def __init__(self, run_id):
        self.run_id = run_id

    def execute_remediation(self, repo_path, anomaly):
        payload = {
            "run_id": self.run_id,
            "target_path": repo_path
        }
        res = run_remediation_pipeline(payload)
        return {"token": f"token-{self.run_id}", "status": res.get("status")}


class RealRestorer:
    def restore_state(self, repo_path, anomaly_id):
        marker = os.path.join(repo_path, f"restored_{anomaly_id}")
        with open(marker, "w") as f:
            f.write("restored")


class TestRepoHealthAnomalyRemediationPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_remediation_pipeline(self):
        pipeline_id = str(uuid.uuid4())
        anomaly_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())

        inspector = RealInspector(expected_anomaly_id=anomaly_id)
        automator = RealAutomator(run_id=run_id)
        restorer = RealRestorer()

        pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=pipeline_id,
            inspector=inspector,
            automator=automator,
            restorer=restorer
        )

        result = pipeline.run_pipeline(self.repo_path)

        self.assertEqual(result.get("pipeline_id"), pipeline_id)
        self.assertEqual(result.get("anomaly_id"), anomaly_id)
        self.assertEqual(result.get("status"), "remediated")
        self.assertEqual(result.get("token"), f"token-{run_id}")

        expected_marker = os.path.join(self.repo_path, f".remediated_{run_id}")
        self.assertTrue(os.path.exists(expected_marker))

        health_result = pipeline.run_pipeline(self.repo_path)
        self.assertEqual(health_result.get("status"), "healthy")
        self.assertFalse(health_result.get("remediated"))

    def test_batch_remediate_integration(self):
        subdirs = []
        for _ in range(random.randint(2, 4)):
            d = tempfile.TemporaryDirectory()
            subdirs.append(d.name)

        try:
            pipeline_id = str(uuid.uuid4())
            anomaly_id = str(uuid.uuid4())
            run_id = str(uuid.uuid4())

            inspector = RealInspector(expected_anomaly_id=anomaly_id)
            automator = RealAutomator(run_id=run_id)

            pipeline = RepoHealthAnomalyRemediationPipeline(
                pipeline_id=pipeline_id,
                inspector=inspector,
                automator=automator
            )

            reports = pipeline.batch_remediate(subdirs)
            self.assertEqual(len(reports), len(subdirs))
            for rep in reports:
                self.assertEqual(rep.get("status"), "remediated")
                self.assertEqual(rep.get("anomaly_id"), anomaly_id)
        finally:
            for d in subdirs:
                try:
                    os.rmdir(d)
                except Exception:
                    pass


if __name__ == "__main__":
    unittest.main()