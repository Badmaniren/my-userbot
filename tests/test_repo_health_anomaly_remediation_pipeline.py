import unittest
from unittest.mock import MagicMock, patch
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
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
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
        self.inspector.inspect_repository.return_value = None

        result = self.pipeline.run_pipeline(self.repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["remediated"])
        self.inspector.inspect_repository.assert_called_once_with(self.repo_path)

    def test_run_pipeline_remediated(self):
        anomaly_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        anomaly = {"anomaly_id": anomaly_id}
        
        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.return_value = {"token": token}

        result = self.pipeline.run_pipeline(self.repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertEqual(result["anomaly_id"], anomaly_id)
        self.assertEqual(result["status"], "remediated")
        self.assertEqual(result["token"], token)
        self.automator.execute_remediation.assert_called_once_with(self.repo_path, anomaly)

    def test_run_pipeline_exception_triggers_restorer(self):
        anomaly_id = uuid.uuid4().hex
        anomaly = {"anomaly_id": anomaly_id}
        error_msg = uuid.uuid4().hex

        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.side_effect = Exception(error_msg)

        with self.assertRaises(RemediationExecutionError) as ctx:
            self.pipeline.run_pipeline(self.repo_path)

        self.assertIn(error_msg, str(ctx.exception))
        self.restorer.restore_state.assert_called_once_with(self.repo_path, anomaly_id)

    def test_analyze_anomaly_stream(self):
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        metric_name = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        random_content = "".join(random.choices(string.ascii_letters + string.digits, k=random.randint(10, 200)))

        mock_file = io.StringIO(random_content)

        with patch("skills.repo_health_anomaly_remediation_pipeline.open", return_value=mock_file):
            result = self.pipeline.analyze_anomaly_stream(log_path, metric_name, threshold)

        self.assertTrue(result["stream_processed"])
        self.assertEqual(result["metric"], metric_name)
        self.assertIsInstance(result["anomaly_score"], float)

    def test_batch_remediate(self):
        repo_paths = [f"/tmp/{uuid.uuid4().hex}" for _ in range(3)]
        
        self.inspector.inspect_repository.return_value = None

        reports = self.pipeline.batch_remediate(repo_paths)

        self.assertEqual(len(reports), len(repo_paths))
        for report in reports:
            self.assertEqual(report["status"], "healthy")

    def test_run_remediation_pipeline(self):
        run_id = uuid.uuid4().hex
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {
            "run_id": run_id,
            "target_path": target_path
        }

        with patch("os.path.exists", return_value=False), \
             patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", create=True) as mock_open:
            
            result = run_remediation_pipeline(payload)

            mock_makedirs.assert_called_once_with(target_path, exist_ok=True)
            mock_open.assert_called_once_with(os.path.join(target_path, f".remediated_{run_id}"), "w")
            self.assertEqual(result["run_id"], run_id)
            self.assertEqual(result["status"], "remediated")

    def test_inspect_anomalies_detected(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {"target_path": target_path}

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[uuid.uuid4().hex, uuid.uuid4().hex]):
            
            result = inspect_anomalies(payload)
            self.assertTrue(result["anomaly_detected"])

    def test_inspect_anomalies_not_detected(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        run_id = uuid.uuid4().hex
        payload = {"target_path": target_path}

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[uuid.uuid4().hex, f".remediated_{run_id}"]):
            
            result = inspect_anomalies(payload)
            self.assertFalse(result["anomaly_detected"])