import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.repo_health_anomaly_remediation_pipeline import (
    RepoHealthAnomalyRemediationPipeline,
    RemediationError
)

class TestRepoHealthAnomalyRemediationPipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo_{uuid.uuid4().hex[:8]}"
        self.pipeline = RepoHealthAnomalyRemediationPipeline(repo_path=self.repo_path)

    def test_run_remediation_success_flow(self):
        anomaly_id = uuid.uuid4().hex
        severity = random.choice(["HIGH", "CRITICAL", "MODERATE"])
        anomaly_type = f"anomaly_type_{uuid.uuid4().hex[:6]}"

        mock_inspector = MagicMock()
        mock_inspector.inspect.return_value = [
            {"id": anomaly_id, "type": anomaly_type, "severity": severity}
        ]

        mock_restorer = MagicMock()
        mock_restorer.restore.return_value = True

        mock_committer = MagicMock()
        mock_committer.commit_changes.return_value = uuid.uuid4().hex

        with patch('skills.repo_health_anomaly_remediation_pipeline.repo_health_anomaly_inspector', mock_inspector), \
             patch('skills.repo_health_anomaly_remediation_pipeline.repo_health_restorer', mock_restorer), \
             patch('skills.repo_health_anomaly_remediation_pipeline.repo_auto_committer', mock_committer):

            result = self.pipeline.execute_remediation_cycle()

            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("remediated_count"), 1)
            mock_inspector.inspect.assert_called_once_with(self.repo_path)
            mock_restorer.restore.assert_called_once()
            mock_committer.commit_changes.assert_called_once()

    def test_run_remediation_no_anomalies(self):
        mock_inspector = MagicMock()
        mock_inspector.inspect.return_value = []

        with patch('skills.repo_health_anomaly_remediation_pipeline.repo_health_anomaly_inspector', mock_inspector):
            result = self.pipeline.execute_remediation_cycle()

            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("remediated_count"), 0)

    def test_remediation_failure_raises_exception(self):
        anomaly_id = uuid.uuid4().hex
        mock_inspector = MagicMock()
        mock_inspector.inspect.return_value = [
            {"id": anomaly_id, "type": "memory_leak", "severity": "CRITICAL"}
        ]

        mock_restorer = MagicMock()
        mock_restorer.restore.return_value = False

        with patch('skills.repo_health_anomaly_remediation_pipeline.repo_health_anomaly_inspector', mock_inspector), \
             patch('skills.repo_health_anomaly_remediation_pipeline.repo_health_restorer', mock_restorer):

            with self.assertRaises(RemediationError):
                self.pipeline.execute_remediation_cycle()

    def test_multi_step_remediation_with_fallback(self):
        anomaly_id_1 = uuid.uuid4().hex
        anomaly_id_2 = uuid.uuid4().hex

        mock_inspector = MagicMock()
        mock_inspector.inspect.return_value = [
            {"id": anomaly_id_1, "type": "disk_space", "severity": "HIGH"},
            {"id": anomaly_id_2, "type": "cpu_spike", "severity": "MEDIUM"}
        ]

        mock_restorer = MagicMock()
        # Первый шаг падает, второй успешен
        mock_restorer.restore.side_effect = [False, True]

        mock_optimizer = MagicMock()
        mock_optimizer.optimize.return_value = {"status": "optimized", "bytes_freed": random.randint(1024, 819200)}

        with patch('skills.repo_health_anomaly_remediation_pipeline.repo_health_anomaly_inspector', mock_inspector), \
             patch('skills.repo_health_anomaly_remediation_pipeline.repo_health_restorer', mock_restorer), \
             patch('skills.repo_health_anomaly_remediation_pipeline.repo_health_optimizer', mock_optimizer):

            result = self.pipeline.execute_remediation_cycle()
            self.assertTrue(result.get("partial_success"))
            self.assertEqual(result.get("remediated_count"), 1)
            mock_optimizer.optimize.assert_called_once()

    def test_io_stream_log_parsing_during_remediation(self):
        random_error_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        log_content = f"CRITICAL_FAILURE: {random_error_code} detected in pipeline."
        stream = io.BytesIO(log_content.encode('utf-8'))

        mock_logger = MagicMock()
        mock_logger.read_latest_logs.return_value = stream

        with patch('skills.repo_health_anomaly_remediation_pipeline.repo_logger', mock_logger):
            parsed_data = self.pipeline.analyze_error_stream()
            self.assertIn(random_error_code, parsed_data)
            self.assertEqual(parsed_data["error_code"], random_error_code)

if __name__ == '__main__':
    unittest.main()