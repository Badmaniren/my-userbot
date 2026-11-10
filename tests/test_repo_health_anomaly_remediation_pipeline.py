import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import os
import io

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

    def test_run_pipeline_healthy_repository(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector.inspect_repository.return_value = None
        
        result = self.pipeline.run_pipeline(repo_path)
        
        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["remediated"])
        self.inspector.inspect_repository.assert_called_once_with(repo_path)
        self.automator.execute_remediation.assert_not_called()

    def test_run_pipeline_remediated_successfully(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        
        anomaly = {"anomaly_id": anomaly_id}
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

    def test_run_pipeline_remediation_failure_triggers_restoration(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        error_message = uuid.uuid4().hex
        
        anomaly = {"anomaly_id": anomaly_id}
        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.side_effect = RuntimeError(error_message)
        
        with self.assertRaises(RemediationExecutionError) as ctx:
            self.pipeline.run_pipeline(repo_path)
            
        self.assertIn(error_message, str(ctx.exception))
        self.inspector.inspect_repository.assert_called_once_with(repo_path)
        self.automator.execute_remediation.assert_called_once_with(repo_path, anomaly)
        self.restorer.restore_state.assert_called_once_with(repo_path, anomaly_id)

    def test_analyze_anomaly_stream_parses_content(self):
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        metric_name = uuid.uuid4().hex
        threshold = random.uniform(10.0, 100.0)
        random_content = uuid.uuid4().hex * 5
        
        mock_file = io.StringIO(random_content)
        
        with patch("builtins.open", return_value=mock_file):
            result = self.pipeline.analyze_anomaly_stream(log_path, metric_name, threshold)
            
        self.assertTrue(result["stream_processed"])
        self.assertEqual(result["metric"], metric_name)
        expected_score = float(len(random_content) % 100) / 100.0 * threshold
        self.assertEqual(result["anomaly_score"], expected_score)

    def test_batch_remediate_executes_multiple_pipelines(self):
        paths = [f"/tmp/{uuid.uuid4().hex}" for _ in range(3)]
        
        with patch.object(self.pipeline, "run_pipeline") as mock_run:
            expected_reports = [{"path": p, "status": "remediated"} for p in paths]
            mock_run.side_effect = expected_reports
            
            reports = self.pipeline.batch_remediate(paths)
            
            self.assertEqual(reports, expected_reports)
            self.assertEqual(mock_run.call_count, len(paths))
            for path in paths:
                mock_run.assert_any_call(path)

    def test_run_remediation_pipeline_utility(self):
        run_id = uuid.uuid4().hex
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {
            "run_id": run_id,
            "target_path": target_path
        }
        
        with patch("os.path.exists", return_value=False) as mock_exists,