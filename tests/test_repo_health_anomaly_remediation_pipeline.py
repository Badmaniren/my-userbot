import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
import io
import uuid
import random
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
        self.pipeline_id = str(uuid.uuid4())
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
        repo_path = f"/path/to/{uuid.uuid4().hex}"
        self.inspector.inspect_repository.return_value = None

        result = self.pipeline.run_pipeline(repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["remediated"])
        self.inspector.inspect_repository.assert_called_once_with(repo_path)
        self.automator.execute_remediation.assert_not_called()

    def test_run_pipeline_remediated(self):
        repo_path = f"/path/to/{uuid.uuid4().hex}"
        anomaly_id = str(uuid.uuid4())
        token = str(uuid.uuid4())

        anomaly = {"anomaly_id": anomaly_id, "severity": AnomalySeverity.HIGH.name}
        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.return_value = {"token": token}

        result = self.pipeline.run_pipeline(repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["repo_path"], repo_path)
        self.assertEqual(result["anomaly_id"], anomaly_id)
        self.assertEqual(result["status"], "remediated")
        self.assertEqual(result["token"], token)
        
        self.inspector.inspect_repository.assert_called_once_with(repo_path)
        self.automator.execute_remediation.assert_called_once_with(repo_path, anomaly)
        self.restorer.restore_state.assert_not_called()

    def test_run_pipeline_execution_error_with_restoration(self):
        repo_path = f"/path/to/{uuid.uuid4().hex}"
        anomaly_id = str(uuid.uuid4())
        error_message = f"error_{uuid.uuid4().hex}"

        anomaly = {"anomaly_id": anomaly_id}
        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.side_effect = RuntimeError(error_message)

        with self.assertRaises(RemediationExecutionError) as ctx:
            self.pipeline.run_pipeline(repo_path)

        self.assertIn(error_message, str(ctx.exception))
        self.restorer.restore_state.assert_called_once_with(repo_path, anomaly_id)

    def test_analyze_anomaly_stream(self):
        log_path = f"/logs/{uuid.uuid4().hex}.log"
        metric_name = f"metric_{uuid.uuid4().hex}"
        threshold = random.uniform(1.0, 100.0)
        
        random_content = "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(10, 50)))

        with patch("builtins.open", mock_open(read_data=random_content)):
            result = self.pipeline.analyze_anomaly_stream(log_path, metric_name, threshold)

        self.assertTrue(result["stream_processed"])
        self.assertEqual(result["metric"], metric_name)
        self.assertIsInstance(result["anomaly_score"], float)

    def test_batch_remediate(self):
        repo_paths = [f"/repo/{uuid.uuid4().hex}" for _ in range(3)]
        
        self.inspector.inspect_repository.return_value = None

        reports = self.pipeline.batch_remediate(repo_paths)

        self.assertEqual(len(reports), len(repo_paths))
        for report in reports:
            self.assertEqual(report["status"], "healthy")
            self.assertFalse(report["remediated"])

    def test_run_remediation_pipeline(self):
        run_id = uuid.uuid4().hex
        target_path = f"/tmp/{uuid.uuid4().hex}"

        with patch("os.path.exists", return_value=False), \
             patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mock_file:
            
            payload = {"run_id": run_id, "target_path": target_path}
            result = run_remediation_pipeline(payload)

            self.assertEqual(result["run_id"], run_id)
            self.assertEqual(result["status"], "remediated")
            mock_makedirs.assert_called_once_with(target_path, exist_ok=True)
            mock_file.assert_called_once()

    def test_inspect_anomalies_detected(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        
        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[f"file_{uuid.uuid4().hex}.txt"]):
            
            payload = {"target_path": target_path}
            result = inspect_anomalies(payload)

            self.assertTrue(result["anomaly_detected"])

    def test_inspect_anomalies_not_detected(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        remediated_file = f".remediated_{uuid.uuid4().hex}"

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[remediated_file, f"other_{uuid.uuid4().hex}"]):
            
            payload = {"target_path": target_path}
            result = inspect_anomalies(payload)

            self.assertFalse(result["anomaly_detected"])

if __name__ == "__main__":
    unittest.main()