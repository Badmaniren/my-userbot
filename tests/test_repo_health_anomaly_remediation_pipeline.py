import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import os
import io
import tempfile

from skills.repo_health_anomaly_remediation_pipeline import (
    AnomalySeverity,
    RemediationExecutionError,
    RepoHealthAnomalyRemediationPipeline,
    run_remediation_pipeline,
    inspect_anomalies
)


class TestRepoHealthAnomalyRemediationPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline_id = uuid.uuid4().hex
        self.inspector = MagicMock()
        self.automator = MagicMock()
        self.restorer = MagicMock()
        self.logger = MagicMock()
        
        self.pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=self.inspector,
            automator=self.automator,
            restorer=self.restorer,
            logger=self.logger
        )

    def test_run_pipeline_healthy(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector.inspect_repository.return_value = None

        result = self.pipeline.run_pipeline(repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["remediated"])
        self.inspector.inspect_repository.assert_called_once_with(repo_path)

    def test_run_pipeline_remediated(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        token = uuid.uuid4().hex

        self.inspector.inspect_repository.return_value = {"anomaly_id": anomaly_id}
        self.automator.execute_remediation.return_value = {"token": token}

        result = self.pipeline.run_pipeline(repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["repo_path"], repo_path)
        self.assertEqual(result["anomaly_id"], anomaly_id)
        self.assertEqual(result["status"], "remediated")
        self.assertEqual(result["token"], token)
        self.automator.execute_remediation.assert_called_once()

    def test_run_pipeline_remediation_failure_with_restorer(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        error_message = uuid.uuid4().hex

        self.inspector.inspect_repository.return_value = {"anomaly_id": anomaly_id}
        self.automator.execute_remediation.side_effect = Exception(error_message)

        with self.assertRaises(RemediationExecutionError) as ctx:
            self.pipeline.run_pipeline(repo_path)

        self.assertIn(error_message, str(ctx.exception))
        self.restorer.restore_state.assert_called_once_with(repo_path, anomaly_id)

    def test_analyze_anomaly_stream(self):
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        metric_name = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        random_content = "".join(random.choices("ABCDEF0123456789", k=random.randint(10, 50)))

        with patch("builtins.open", unittest.mock.mock_open(read_data=random_content)):
            result = self.pipeline.analyze_anomaly_stream(log_path, metric_name, threshold)

        self.assertTrue(result["stream_processed"])
        self.assertEqual(result["metric"], metric_name)
        self.assertIsInstance(result["anomaly_score"], float)

    def test_batch_remediate(self):
        repo_paths = [f"/tmp/{uuid.uuid4().hex}" for _ in range(3)]
        self.inspector.inspect_repository.return_value = None

        reports = self.pipeline.batch_remediate(repo_paths)

        self.assertEqual(len(reports), 3)
        for report in reports:
            self.assertEqual(report["status"], "healthy")

    def test_run_remediation_pipeline_function(self):
        run_id = uuid.uuid4().hex
        target_path = tempfile.mkdtemp()
        payload = {
            "run_id": run_id,
            "target_path": target_path
        }

        try:
            res = run_remediation_pipeline(payload)
            self.assertEqual(res["run_id"], run_id)
            self.assertEqual(res["status"], "remediated")
            
            marker_file = os.path.join(target_path, f".remediated_{run_id}")
            self.assertTrue(os.path.exists(marker_file))
        finally:
            if os.path.exists(target_path):
                for f in os.listdir(target_path):
                    os.remove(os.path.join(target_path, f))
                os.rmdir(target_path)

    def test_inspect_anomalies_function(self):
        target_path = tempfile.mkdtemp()
        run_id = uuid.uuid4().hex
        payload = {
            "target_path": target_path
        }

        try:
            res_before = inspect_anomalies(payload)
            self.assertTrue(res_before["anomaly_detected"])

            marker_file = os.path.join(target_path, f".remediated_{run_id}")
            with open(marker_file, "w") as f:
                f.write(uuid.uuid4().hex)

            res_after = inspect_anomalies(payload)
            self.assertFalse(res_after["anomaly_detected"])
        finally:
            if os.path.exists(target_path):
                for f in os.listdir(target_path):
                    os.remove(os.path.join(target_path, f))
                os.rmdir(target_path)


if __name__ == "__main__":
    unittest.main()