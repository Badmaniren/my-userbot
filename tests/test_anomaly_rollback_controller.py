import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
from skills.anomaly_rollback_controller import (
    AnomalyRollbackController,
    AnomalyRollbackControllerError
)

class TestAnomalyRollbackController(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo/{uuid.uuid4().hex}"
        self.rand_log = f"/var/log/{uuid.uuid4().hex}.log"
        self.rand_threshold = round(random.uniform(0.1, 0.9), 2)
        self.controller = AnomalyRollbackController(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

    def test_init_sets_attributes(self):
        self.assertEqual(self.controller.repo_path, self.rand_repo)
        self.assertEqual(self.controller.log_path, self.rand_log)
        self.assertEqual(self.controller.threshold, self.rand_threshold)

    def test_rollback_execution_success(self):
        rand_commit = uuid.uuid4().hex
        rand_anomaly_id = uuid.uuid4().hex
        rand_source = ''.join(random.choices(string.ascii_letters, k=8))
        
        mock_git_inspector_instance = MagicMock()
        mock_git_inspector_instance.get_latest_changes.return_value = rand_commit
        
        with patch('skills.anomaly_rollback_controller.GitInspector', return_value=mock_git_inspector_instance) as mock_git_cls, \
             patch('skills.anomaly_rollback_controller.AnomalyLogger') as mock_logger_cls:
            
            mock_logger_instance = mock_logger_cls.return_value
            
            result = self.controller.execute_rollback(rand_anomaly_id, rand_source)
            
            self.assertTrue(result)
            mock_git_cls.assert_called_once_with(self.rand_repo)
            mock_git_inspector_instance.get_latest_changes.assert_called_once()
            mock_logger_instance.log_anomaly.assert_called_once()
            
            args, _ = mock_logger_instance.log_anomaly.call_args
            self.assertEqual(args[0], rand_source)
            self.assertIn(rand_anomaly_id, args[2])
            self.assertIn(rand_commit, args[2])

    def test_rollback_execution_failure_raises_custom_error(self):
        rand_anomaly_id = uuid.uuid4().hex
        rand_source = ''.join(random.choices(string.ascii_lowercase, k=10))
        rand_error_msg = uuid.uuid4().hex

        with patch('skills.anomaly_rollback_controller.GitInspector', side_effect=Exception(rand_error_msg)):
            with self.assertRaises(AnomalyRollbackControllerError) as ctx:
                self.controller.execute_rollback(rand_anomaly_id, rand_source)
            
            self.assertIn(rand_error_msg, str(ctx.exception))

    def test_verify_rollback_integrity_positive(self):
        rand_metric = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_value = round(random.uniform(1.0, 50.0), 2)
        rand_stream_data = io.BytesIO(f"telemetry_{uuid.uuid4().hex}".encode('utf-8'))

        mock_audit_hub_instance = MagicMock()
        mock_audit_hub_instance.aggregate_and_report.return_value = True

        with patch('skills.anomaly_rollback_controller.AnomalyAuditHub', return_value=mock_audit_hub_instance) as mock_hub_cls:
            status = self.controller.verify_rollback_integrity(rand_metric, rand_value, rand_stream_data)
            
            self.assertTrue(status)
            mock_hub_cls.assert_called_once_with(repo_path=self.rand_repo, log_path=self.rand_log, threshold=self.rand_threshold)
            mock_audit_hub_instance.aggregate_and_report.assert_called_once_with(rand_metric, rand_value)

    def test_verify_rollback_integrity_negative(self):
        rand_metric = ''.join(random.choices(string.ascii_uppercase, k=6))
        rand_value = round(random.uniform(51.0, 100.0), 2)
        rand_stream_data = io.BytesIO(b"garbage_data_stream")

        mock_audit_hub_instance = MagicMock()
        mock_audit_hub_instance.aggregate_and_report.side_effect = Exception("Audit Hub failure")

        with patch('skills.anomaly_rollback_controller.AnomalyAuditHub', return_value=mock_audit_hub_instance):
            with self.assertRaises(AnomalyRollbackControllerError):
                self.controller.verify_rollback_integrity(rand_metric, rand_value, rand_stream_data)

    def test_finalize_epic_restoration_report(self):
        rand_report_key = uuid.uuid4().hex
        rand_report_val = uuid.uuid4().hex
        
        mock_audit_hub_instance = MagicMock()
        mock_audit_hub_instance.generate_final_report.return_value = {rand_report_key: rand_report_val}

        with patch('skills.anomaly_rollback_controller.AnomalyAuditHub', return_value=mock_audit_hub_instance):
            report = self.controller.finalize_epic_restoration()
            
            self.assertIsInstance(report, dict)
            self.assertEqual(report.get(rand_report_key), rand_report_val)
            mock_audit_hub_instance.generate_final_report.assert_called_once()

    def test_finalize_epic_restoration_exception_handling(self):
        mock_audit_hub_instance = MagicMock()
        mock_audit_hub_instance.generate_final_report.side_effect = KeyError("Missing log data")

        with patch('skills.anomaly_rollback_controller.AnomalyAuditHub', return_value=mock_audit_hub_instance):
            with self.assertRaises(AnomalyRollbackControllerError):
                self.controller.finalize_epic_restoration()

if __name__ == '__main__':
    unittest.main()