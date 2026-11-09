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

        self.inspector.inspect_repository.assert_called_once_with(repo_path)
        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("status"), "healthy")
        self.assertFalse(result.get("remediated"))

    def test_run_pipeline_remediated_anomaly(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        token = uuid.uuid4().hex
        
        anomaly = {"anomaly_id": anomaly_id, "severity": AnomalySeverity.HIGH.name}
        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.return_value = {"token": token}

        result = self.pipeline.run_pipeline(repo_path)

        self.inspector.inspect_repository.assert_called_once_with(repo_path)
        self.automator.execute_remediation.assert_called_once_with(repo_path, anomaly)
        
        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("repo_path"), repo_path)
        self.assertEqual(result.get("anomaly_id"), anomaly_id)
        self.assertEqual(result.get("status"), "remediated")
        self.assertEqual(result.get("token"), token)

    def test_run_pipeline_remediation_failure_triggers_restorer(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        error_message = uuid.uuid4().hex

        anomaly = {"anomaly_id": anomaly_id}
        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.side_effect = Exception(error_message)

        with self.assertRaises(RemediationExecutionError) as ctx:
            self.pipeline.run_pipeline(repo_path)

        self.assertIn(error_message, str(ctx.exception))
        self.restorer.restore_state.assert_called_once_with(repo_path, anomaly_id)

    def test_analyze_anomaly_stream_success(self):
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        metric_name = uuid.uuid4().hex
        threshold = random.uniform(10.0, 100.0)
        random_content = "".join(random.choices(string.ascii_letters, k=random.randint(15, 50)))

        mock_file = io.StringIO(random_content)
        with patch("builtins.open", return_value=mock_file):
            result = self.pipeline.analyze_anomaly_stream(log_path, metric_name, threshold)

        self.assertTrue(result.get("stream_processed"))
        self.assertEqual(result.get("metric"), metric_name)
        self.assertIsInstance(result.get("anomaly_score"), float)

    def test_batch_remediate_pipeline(self):
        repo_paths = [f"/tmp/{uuid.uuid4().hex}" for _ in range(random.randint(2, 5))]
        
        with patch.object(self.pipeline, "run_pipeline") as mock_run:
            expected_results = [{"pipeline_id": self.pipeline_id, "status": "healthy"} for _ in repo_paths]
            mock_run.side_effect = expected_results

            reports = self.pipeline.batch_remediate(repo_paths)

            self.assertEqual(reports, expected_results)
            self.assertEqual(mock_run.call_count, len(repo_paths))

    def test_run_remediation_pipeline_function(self):
        run_id = uuid.uuid4().hex
        target_path = f"/tmp/{uuid.uuid4().hex}"

        payload = {
            "run_id": run_id,
            "target_path": target_path
        }

        mock_file = MagicMock()
        with patch("os.path.join", return_value=f"{target_path}/marker"), \
             patch("builtins.open", return_value=mock_file) as mock_open:
            
            res = run_remediation_pipeline(payload)

            self.assertEqual(res.get("run_id"), run_id)
            self.assertEqual(res.get("status"), "remediated")
            mock_open.assert_called_once_with(f"{target_path}/marker", "w")

    def test_inspect_anomalies_function_no_anomaly(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        run_id = uuid.uuid4().hex
        marker_name = f".remediated_{run_id}"

        payload = {"target_path": target_path}

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[marker_name, uuid.uuid4().hex]):
            
            res = inspect_anomalies(payload)

            self.assertFalse(res.get("anomaly_detected"))

    def test_inspect_anomalies_function_anomaly_detected(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {"target_path": target_path}

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[uuid.uuid4().hex, uuid.uuid4().hex]):
            
            res = inspect_anomalies(payload)

            self.assertTrue(res.get("anomaly_detected"))


if __name__ == "__main__":
    unittest.main()