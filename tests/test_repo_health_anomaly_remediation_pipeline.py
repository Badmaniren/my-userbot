import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.repo_health_anomaly_remediation_pipeline import (
    RepoHealthAnomalyRemediationPipeline,
    RemediationExecutionError,
    AnomalySeverity
)


class TestRepoHealthAnomalyRemediationPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline_id = uuid.uuid4().hex
        self.inspector_mock = MagicMock()
        self.automator_mock = MagicMock()
        self.restorer_mock = MagicMock()
        self.logger_mock = MagicMock()

        self.pipeline = RepoHealthAnomalyRemediationPipeline(
            pipeline_id=self.pipeline_id,
            inspector=self.inspector_mock,
            automator=self.automator_mock,
            restorer=self.restorer_mock,
            logger=self.logger_mock
        )

    def test_run_remediation_pipeline_success(self):
        repo_path = f"/repo/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        anomaly_metric = f"metric_{uuid.uuid4().hex[:8]}"
        severity_value = random.choice(list(AnomalySeverity)).name

        inspector_payload = {
            "anomaly_id": anomaly_id,
            "metric": anomaly_metric,
            "severity": severity_value,
            "score": random.uniform(0.1, 0.9)
        }

        self.inspector_mock.inspect_repository.return_value = inspector_payload
        
        remediation_result_token = uuid.uuid4().hex
        self.automator_mock.execute_remediation.return_value = {
            "status": "success",
            "token": remediation_result_token
        }

        execution_report = self.pipeline.run_pipeline(repo_path)

        self.assertEqual(execution_report["pipeline_id"], self.pipeline_id)
        self.assertEqual(execution_report["repo_path"], repo_path)
        self.assertEqual(execution_report["anomaly_id"], anomaly_id)
        self.assertEqual(execution_report["status"], "remediated")
        self.assertEqual(execution_report["token"], remediation_result_token)
        
        self.inspector_mock.inspect_repository.assert_called_once_with(repo_path)
        self.automator_mock.execute_remediation.assert_called_once()

    def test_run_remediation_pipeline_no_anomalies(self):
        repo_path = f"/repo/{uuid.uuid4().hex}"
        self.inspector_mock.inspect_repository.return_value = None

        execution_report = self.pipeline.run_pipeline(repo_path)

        self.assertEqual(execution_report["pipeline_id"], self.pipeline_id)
        self.assertEqual(execution_report["status"], "healthy")
        self.assertEqual(execution_report["remediated"], False)
        
        self.restorer_mock.restore_state.assert_not_called()

    def test_run_remediation_pipeline_fallback_to_restorer(self):
        repo_path = f"/repo/{uuid.uuid4().hex}"
        anomaly_id = uuid.uuid4().hex
        
        self.inspector_mock.inspect_repository.return_value = {
            "anomaly_id": anomaly_id,
            "severity": AnomalySeverity.CRITICAL.name,
            "score": 0.99
        }

        self.automator_mock.execute_remediation.side_effect = Exception("Fatal remediation error")
        
        restoration_token = uuid.uuid4().hex
        self.restorer_mock.restore_state.return_value = {
            "restored": True,
            "backup_id": restoration_token
        }

        with self.assertRaises(RemediationExecutionError):
            self.pipeline.run_pipeline(repo_path)

        self.restorer_mock.restore_state.assert_called_once_with(repo_path, anomaly_id)

    def test_process_anomaly_stream_with_io_buffer(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)

        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        threshold = random.uniform(50.0, 100.0)

        with patch("skills.repo_health_anomaly_remediation_pipeline.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = mock_stream
            
            result = self.pipeline.analyze_anomaly_stream(f"/var/log/{uuid.uuid4().hex}.log", metric_name, threshold)
            
            self.assertIn("stream_processed", result)
            self.assertEqual(result["metric"], metric_name)
            self.assertIsInstance(result["anomaly_score"], float)

    def test_batch_remediation_execution(self):
        repo_count = random.randint(2, 5)
        repo_paths = [f"/repo/{uuid.uuid4().hex}" for _ in range(repo_count)]
        
        expected_results = []
        for path in repo_paths:
            expected_results.append({
                "repo_path": path,
                "status": "fixed",
                "anomaly_id": uuid.uuid4().hex
            })

        with patch.object(self.pipeline, "run_pipeline") as mock_run:
            mock_run.side_effect = expected_results
            
            batch_report = self.pipeline.batch_remediate(repo_paths)
            
            self.assertEqual(len(batch_report), repo_count)
            for i, res in enumerate(batch_report):
                self.assertEqual(res["repo_path"], repo_paths[i])
                self.assertEqual(res["status"], "fixed")


if __name__ == "__main__":
    unittest.main()