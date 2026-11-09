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
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"

    def test_run_pipeline_healthy_repository(self):
        self.inspector.inspect_repository.return_value = None
        
        result = self.pipeline.run_pipeline(self.repo_path)
        
        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("status"), "healthy")
        self.assertFalse(result.get("remediated"))
        self.inspector.inspect_repository.assert_called_once_with(self.repo_path)
        self.automator.execute_remediation.assert_not_called()

    def test_run_pipeline_anomaly_remediated_successfully(self):
        anomaly_id = uuid.uuid4().hex
        token_val = uuid.uuid4().hex
        anomaly = {"anomaly_id": anomaly_id, "severity": AnomalySeverity.HIGH.name}
        
        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.return_value = {"token": token_val}
        
        result = self.pipeline.run_pipeline(self.repo_path)
        
        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("repo_path"), self.repo_path)
        self.assertEqual(result.get("anomaly_id"), anomaly_id)
        self.assertEqual(result.get("status"), "remediated")
        self.assertEqual(result.get("token"), token_val)
        
        self.inspector.inspect_repository.assert_called_once_with(self.repo_path)
        self.automator.execute_remediation.assert_called_once_with(self.repo_path, anomaly)
        self.restorer.restore_state.assert_not_called()

    def test_run_pipeline_remediation_failure_triggers_restorer(self):
        anomaly_id = uuid.uuid4().hex
        anomaly = {"anomaly_id": anomaly_id, "severity": AnomalySeverity.CRITICAL.name}
        error_message = uuid.uuid4().hex
        
        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.side_effect = Exception(error_message)
        
        with self.assertRaises(RemediationExecutionError) as ctx:
            self.pipeline.run_pipeline(self.repo_path)
            
        self.assertIn(error_message, str(ctx.exception))
        self.restorer.restore_state.assert_called_once_with(self.repo_path, anomaly_id)

    def test_analyze_anomaly_stream_file_reading(self):
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        metric_name = uuid.uuid4().hex
        threshold = random.uniform(10.0, 100.0)
        random_content = uuid.uuid4().hex * random.randint(1, 5)
        
        mock_file_data = io.StringIO(random_content)
        
        with patch("builtins.open", return_value=mock_file_data) as mock_open:
            result = self.pipeline.analyze_anomaly_stream(log_path, metric_name, threshold)
            
            mock_open.assert_called_once_with(log_path, "r")
            self.assertTrue(result.get("stream_processed"))
            self.assertEqual(result.get("metric"), metric_name)
            self.assertIsInstance(result.get("anomaly_score"), float)

    def test_batch_remediate_processes_multiple_paths(self):
        paths = [f"/tmp/{uuid.uuid4().hex}" for _ in range(3)]
        
        self.inspector.inspect_repository.return_value = None
        
        reports = self.pipeline.batch_remediate(paths)
        
        self.assertEqual(len(reports), 3)
        for report in reports:
            self.assertEqual(report.get("status"), "healthy")
            self.assertEqual(report.get("pipeline_id"), self.pipeline_id)
        
        self.assertEqual(self.inspector.inspect_repository.call_count, 3)

    def test_run_remediation_pipeline_utility(self):
        run_id = uuid.uuid4().hex
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {
            "run_id": run_id,
            "target_path": target_path
        }
        
        mock_file = MagicMock()
        with patch("os.path.join", return_value=f"{target_path}/marker") as mock_join, \
             patch("builtins.open", return_value=mock_file) as mock_open:
            
            res = run_remediation_pipeline(payload)
            
            self.assertEqual(res.get("run_id"), run_id)
            self.assertEqual(res.get("status"), "remediated")
            mock_open.assert_called_once()

    def test_inspect_anomalies_utility(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {"target_path": target_path}
        
        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[f".remediated_{uuid.uuid4().hex}"]):
            
            res = inspect_anomalies(payload)
            self.assertFalse(res.get("anomaly_detected"))

        with patch("os.path.exists", return_value=False):
            res_no_path = inspect_anomalies(payload)
            self.assertTrue(res_no_path.get("anomaly_detected"))


if __name__ == "__main__":
    unittest.main()