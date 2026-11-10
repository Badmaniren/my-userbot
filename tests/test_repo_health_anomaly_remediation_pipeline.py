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

    def test_run_pipeline_invalid_path(self):
        for invalid_path in [None, 12345, 98.76, {}]:
            with self.assertRaises(RemediationExecutionError):
                self.pipeline.run_pipeline(invalid_path)

    def test_run_pipeline_healthy_repository(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector.inspect_repository.return_value = None

        result = self.pipeline.run_pipeline(repo_path)

        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("status"), "healthy")
        self.assertFalse(result.get("remediated"))
        self.inspector.inspect_repository.assert_called_once_with(repo_path)

    def test_run_pipeline_remediated_successfully(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        token = uuid.uuid4().hex

        self.inspector.inspect_repository.return_value = {"anomaly_id": anomaly_id}
        self.automator.execute_remediation.return_value = {"token": token}

        result = self.pipeline.run_pipeline(repo_path)

        self.assertEqual(result.get("pipeline_id"), self.pipeline_id)
        self.assertEqual(result.get("repo_path"), repo_path)
        self.assertEqual(result.get("anomaly_id"), anomaly_id)
        self.assertEqual(result.get("status"), "remediated")
        self.assertEqual(result.get("token"), token)
        
        self.automator.execute_remediation.assert_called_once_with(repo_path, {"anomaly_id": anomaly_id})
        self.restorer.restore_state.assert_not_called()

    def test_run_pipeline_remediation_failure_triggers_restore(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        error_message = f"error_{uuid.uuid4().hex}"

        self.inspector.inspect_repository.return_value = {"anomaly_id": anomaly_id}
        self.automator.execute_remediation.side_effect = Exception(error_message)

        with self.assertRaises(RemediationExecutionError) as ctx:
            self.pipeline.run_pipeline(repo_path)

        self.assertIn(error_message, str(ctx.exception))
        self.restorer.restore_state.assert_called_once_with(repo_path, anomaly_id)

    def test_analyze_anomaly_stream_invalid_path(self):
        for invalid_path in [None, 999, [], {}]:
            with self.assertRaises(ValueError):
                self.pipeline.analyze_anomaly_stream(invalid_path, uuid.uuid4().hex, random.uniform(1.0, 100.0))

    def test_analyze_anomaly_stream_valid(self):
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        metric_name = f"metric_{uuid.uuid4().hex}"
        threshold = random.uniform(10.0, 50.0)
        file_content = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(15, 120)))

        with patch("builtins.open", return_value=io.StringIO(file_content)):
            result = self.pipeline.analyze_anomaly_stream(log_path, metric_name, threshold)

        self.assertTrue(result.get("stream_processed"))
        self.assertEqual(result.get("metric"), metric_name)
        expected_score = float(len(file_content) % 100) / 100.0 * threshold
        self.assertEqual(result.get("anomaly_score"), expected_score)

    def test_batch_remediate_invalid_input(self):
        with self.assertRaises(RemediationExecutionError):
            self.pipeline.batch_remediate(uuid.uuid4().hex)

    def test_batch_remediate_valid(self):
        repo_paths = [f"/tmp/{uuid.uuid4().hex}" for _ in range(random.randint(2, 5))]
        
        with patch.object(self.pipeline, "run_pipeline", return_value={"status": "healthy"}) as mock_run:
            reports = self.pipeline.batch_remediate(repo_paths)
            self.assertEqual(len(reports), len(repo_paths))
            self.assertEqual(mock_run.call_count, len(repo_paths))

    def test_run_remediation_pipeline_invalid_payload(self):
        with self.assertRaises(ValueError):
            run_remediation_pipeline(uuid.uuid4().hex)

    def test_run_remediation_pipeline_valid_execution(self):
        run_id = uuid.uuid4().hex
        target_path = f"/tmp/{uuid.uuid4().hex}"

        with patch("os.path.exists", return_value=False), \
             patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            
            res = run_remediation_pipeline({"run_id": run_id, "target_path": target_path})
            
            self.assertEqual(res.get("run_id"), run_id)
            self.assertEqual(res.get("status"), "remediated")
            mock_makedirs.assert_called_once_with(target_path, exist_ok=True)
            mock_file.assert_called_once()

    def test_inspect_anomalies_non_dict_payload(self):
        res = inspect_anomalies(uuid.uuid4().hex)
        self.assertTrue(res.get("anomaly_detected"))

    def test_inspect_anomalies_with_remediation_marker(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        run_id = uuid.uuid4().hex
        marker_name = f".remediated_{run_id}"

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[marker_name, uuid.uuid4().hex]):
            
            res = inspect_anomalies({"target_path": target_path})
            self.assertFalse(res.get("anomaly_detected"))

    def test_inspect_anomalies_without_remediation_marker(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[uuid.uuid4().hex, uuid.uuid4().hex]):
            
            res = inspect_anomalies({"target_path": target_path})
            self.assertTrue(res.get("anomaly_detected"))


if __name__ == "__main__":
    unittest.main()