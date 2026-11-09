import unittest
from unittest.mock import MagicMock, patch
import os
import io
import random
import uuid
import string

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

    def test_anomaly_severity_enum(self):
        self.assertEqual(AnomalySeverity.LOW.value, 1)
        self.assertEqual(AnomalySeverity.MEDIUM.value, 2)
        self.assertEqual(AnomalySeverity.HIGH.value, 3)
        self.assertEqual(AnomalySeverity.CRITICAL.value, 4)

    def test_run_pipeline_healthy_repo(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector.inspect_repository.return_value = None

        result = self.pipeline.run_pipeline(repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["remediated"])
        self.inspector.inspect_repository.assert_called_once_with(repo_path)

    def test_run_pipeline_remediated_repo(self):
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
        self.automator.execute_remediation.assert_called_once_with(repo_path, {"anomaly_id": anomaly_id})

    def test_run_pipeline_remediation_failure(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        error_message = f"error_{uuid.uuid4().hex}"
        
        self.inspector.inspect_repository.return_value = {"anomaly_id": anomaly_id}
        self.automator.execute_remediation.side_effect = Exception(error_message)

        with self.assertRaises(RemediationExecutionError) as ctx:
            self.pipeline.run_pipeline(repo_path)

        self.assertIn(error_message, str(ctx.exception))
        self.restorer.restore_state.assert_called_once_with(repo_path, anomaly_id)

    def test_analyze_anomaly_stream(self):
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        metric_name = f"metric_{uuid.uuid4().hex}"
        threshold = random.uniform(1.0, 100.0)
        
        random_content = "".join(random.choices(string.ascii_letters, k=random.randint(1, 200)))

        with patch("builtins.open", unittest.mock.mock_open(read_data=random_content)):
            result = self.pipeline.analyze_anomaly_stream(log_path, metric_name, threshold)

        self.assertTrue(result["stream_processed"])
        self.assertEqual(result["metric"], metric_name)
        expected_score = float(len(random_content) % 100) / 100.0 * threshold
        self.assertEqual(result["anomaly_score"], expected_score)

    def test_batch_remediate(self):
        paths = [f"/tmp/{uuid.uuid4().hex}" for _ in range(3)]
        
        with patch.object(self.pipeline, "run_pipeline") as mock_run:
            expected_results = [{"pipeline_id": self.pipeline_id, "status": "healthy", "remediated": False} for _ in paths]
            mock_run.side_effect = expected_results

            results = self.pipeline.batch_remediate(paths)

            self.assertEqual(results, expected_results)
            self.assertEqual(mock_run.call_count, len(paths))

    def test_run_remediation_pipeline(self):
        run_id = uuid.uuid4().hex
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {
            "run_id": run_id,
            "target_path": target_path
        }

        with patch("os.path.join", return_value=f"{target_path}/.remediated_{run_id}") as mock_join, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            
            res = run_remediation_pipeline(payload)

            self.assertEqual(res["run_id"], run_id)
            self.assertEqual(res["status"], "remediated")
            mock_file.assert_called_once_with(f"{target_path}/.remediated_{run_id}", "w")

    def test_inspect_anomalies_no_target(self):
        payload = {"target_path": f"/nonexistent_{uuid.uuid4().hex}"}
        
        with patch("os.path.exists", return_value=False):
            res = inspect_anomalies(payload)
            self.assertTrue(res["anomaly_detected"])

    def test_inspect_anomalies_with_remediation(self):
        run_id = uuid.uuid4().hex
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {"target_path": target_path}

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[f".remediated_{run_id}", f"file_{uuid.uuid4().hex}"]):
            
            res = inspect_anomalies(payload)
            self.assertFalse(res["anomaly_detected"])

    def test_inspect_anomalies_without_remediation(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {"target_path": target_path}

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[f"file_{uuid.uuid4().hex}", f"other_{uuid.uuid4().hex}"]):
            
            res = inspect_anomalies(payload)
            self.assertTrue(res["anomaly_detected"])

if __name__ == "__main__":
    unittest.main()