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

    def test_init_and_logging(self):
        log_msg = uuid.uuid4().hex
        self.pipeline._log(log_msg)
        self.logger.log.assert_called_once_with(log_msg)

    def test_run_pipeline_invalid_path(self):
        for invalid in [None, 12345, 99.9, {}]:
            with self.assertRaises(RemediationExecutionError):
                self.pipeline.run_pipeline(invalid)

    def test_run_pipeline_no_anomaly(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector.inspect_repository.return_value = None

        result = self.pipeline.run_pipeline(repo_path)

        self.assertEqual(result["pipeline_id"], self.pipeline_id)
        self.assertEqual(result["status"], "healthy")
        self.assertFalse(result["remediated"])
        self.inspector.inspect_repository.assert_called_once_with(repo_path)

    def test_run_pipeline_with_anomaly_success(self):
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
        self.automator.execute_remediation.assert_called_once_with(repo_path, anomaly)

    def test_run_pipeline_remediation_failure(self):
        repo_path = f"/tmp/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        anomaly = {"anomaly_id": anomaly_id}
        error_msg = uuid.uuid4().hex

        self.inspector.inspect_repository.return_value = anomaly
        self.automator.execute_remediation.side_effect = Exception(error_msg)

        with self.assertRaises(RemediationExecutionError) as ctx:
            self.pipeline.run_pipeline(repo_path)

        self.assertIn(error_msg, str(ctx.exception))
        self.restorer.restore_state.assert_called_once_with(repo_path, anomaly_id)

    def test_analyze_anomaly_stream_invalid_path(self):
        for invalid in [None, 123, []]:
            with self.assertRaises(ValueError):
                self.pipeline.analyze_anomaly_stream(invalid, uuid.uuid4().hex, random.random())

    def test_analyze_anomaly_stream_success(self):
        log_path = f"/tmp/{uuid.uuid4().hex}.log"
        metric_name = uuid.uuid4().hex
        threshold = random.uniform(1.0, 100.0)
        file_content = uuid.uuid4().hex

        with patch("builtins.open", return_value=io.StringIO(file_content)):
            result = self.pipeline.analyze_anomaly_stream(log_path, metric_name, threshold)

        self.assertTrue(result["stream_processed"])
        self.assertEqual(result["metric"], metric_name)
        expected_score = float(len(file_content) % 100) / 100.0 * threshold
        self.assertEqual(result["anomaly_score"], expected_score)

    def test_batch_remediate_invalid_input(self):
        with self.assertRaises(RemediationExecutionError):
            self.pipeline.batch_remediate(uuid.uuid4().hex)

    def test_batch_remediate_success(self):
        repo_paths = [f"/tmp/{uuid.uuid4().hex}" for _ in range(random.randint(2, 5))]
        
        with patch.object(self.pipeline, "run_pipeline") as mock_run:
            mock_run.side_effect = lambda p: {"path": p, "status": "remediated"}
            results = self.pipeline.batch_remediate(repo_paths)

        self.assertEqual(len(results), len(repo_paths))
        self.assertEqual(mock_run.call_count, len(repo_paths))

    def test_run_remediation_pipeline_invalid_payload(self):
        with self.assertRaises(ValueError):
            run_remediation_pipeline(uuid.uuid4().hex)

    def test_run_remediation_pipeline_execution(self):
        run_id = uuid.uuid4().hex
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {"run_id": run_id, "target_path": target_path}

        with patch("os.path.exists", return_value=False), \
             patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            
            res = run_remediation_pipeline(payload)

        self.assertEqual(res["run_id"], run_id)
        self.assertEqual(res["status"], "remediated")
        mock_makedirs.assert_called_once_with(target_path, exist_ok=True)
        mock_file.assert_called_once_with(os.path.join(target_path, f".remediated_{run_id}"), "w")

    def test_inspect_anomalies_non_dict_payload(self):
        res = inspect_anomalies(uuid.uuid4().hex)
        self.assertTrue(res["anomaly_detected"])

    def test_inspect_anomalies_with_remediated_file(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        run_id = uuid.uuid4().hex
        payload = {"target_path": target_path}

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[f".remediated_{run_id}", uuid.uuid4().hex]):
            res = inspect_anomalies(payload)

        self.assertFalse(res["anomaly_detected"])

    def test_inspect_anomalies_without_remediated_file(self):
        target_path = f"/tmp/{uuid.uuid4().hex}"
        payload = {"target_path": target_path}

        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=[uuid.uuid4().hex, uuid.uuid4().hex]):
            res = inspect_anomalies(payload)

        self.assertTrue(res["anomaly_detected"])


if __name__ == "__main__":
    unittest.main()