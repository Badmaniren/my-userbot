import unittest
from unittest.mock import patch, MagicMock
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
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"

    def test_run_pipeline_healthy(self):
        self.inspector.inspect_repository.return_value = None
        result = self.pipeline.run_pipeline(self.repo_path)
        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("status"), "healthy")
        self.assertFalse(result.get("remediated"))
        self.inspector.inspect_repository.assert_called_once_with(self.repo_path)

    def test_run_pipeline_remediated_success(self):
        anomaly_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        anomaly = {"anomaly_id": anomaly_id, "severity": AnomalySeverity.HIGH.name}
        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.return_value = {"token": token}

        result = self.pipeline.run_pipeline(self.repo_path)
        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("repo_path"), self.repo_path)
        self.assertEqual(result.get("anomaly_id"), anomaly_id)
        self.assertEqual(result.get("status"), "remediated")
        self.assertEqual(result.get("token"), token)
        self.automator.execute_remediation.assert_called_once_with(self.repo_path, anomaly)

    def test_run_pipeline_remediation_failure_and_restore(self):
        anomaly_id = uuid.uuid4().hex
        anomaly = {"anomaly_id": anomaly_id, "severity": AnomalySeverity.CRITICAL.name}
        self.inspector.inspect_repository.return_value = anomaly
        error_message = uuid.uuid4().hex
        self.automator.execute_remediation.side_effect = Exception(error_message)

        with self.assertRaises(RemediationExecutionError) as ctx:
            self.pipeline.run_pipeline(self.repo_path)
        
        self.assertIn(error_message, str(ctx.exception))
        self.restorer.restore_state.assert_called_once_with(self.repo_path, anomaly_id)

    def test_analyze_anomaly_stream(self):
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        metric_name = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        random_content = "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(10, 50)))

        with patch("builtins.open", unittest.mock.mock_open(read_data=random_content)):
            result = self.pipeline.analyze_anomaly_stream(log_path, metric_name, threshold)
        
        self.assertTrue(result.get("stream_processed"))
        self.assertEqual(result.get("metric"), metric_name)
        self.assertIn("anomaly_score", result)
        self.assertIsInstance(result.get("anomaly_score"), float)

    def test_batch_remediate(self):
        paths = [f"/tmp/{uuid.uuid4().hex}" for _ in range(3)]
        self.inspector.inspect_repository.return_value = None

        reports = self.pipeline.batch_remediate(paths)
        self.assertEqual(len(reports), 3)
        for report in reports:
            self.assertEqual(report.get("status"), "healthy")

    def test_run_remediation_pipeline_function(self):
        run_id = uuid.uuid4().hex
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {"run_id": run_id, "target_path": target_path}

        with patch("os.path.join", return_value=f"{target_path}/marker"):
            with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
                res = run_remediation_pipeline(payload)
                self.assertEqual(res.get("run_id"), run_id)
                self.assertEqual(res.get("status"), "remediated")
                mock_file.assert_called_once()

    def test_inspect_anomalies_function(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {"target_path": target_path}

        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=[f".remediated_{uuid.uuid4().hex}", "other_file"]):
                res = inspect_anomalies(payload)
                self.assertFalse(res.get("anomaly_anomaly_detected", False) if "anomaly_anomaly_detected" in res else res.get("anomaly_detected"))

        with patch("os.path.exists", return_value=True):
            with patch("os.listdir", return_value=["random_file.txt"]):
                res = inspect_anomalies(payload)
                self.assertTrue(res.get("anomaly_detected"))