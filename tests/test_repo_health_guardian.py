import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.repo_health_guardian import RepoHealthGuardian

class TestRepoHealthGuardian(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/repo/{uuid.uuid4().hex}/{random.randint(1000, 9999)}"
        
    @patch('skills.repo_health_guardian.RepoMonitor')
    @patch('skills.repo_health_guardian.RepoAuditor')
    def test_init_sets_paths_and_components(self, mock_auditor_class, mock_monitor_class):
        instance = RepoHealthGuardian(self.random_repo_path)
        self.assertEqual(instance.repo_path, self.random_repo_path)
        mock_monitor_class.assert_called_once_with(self.random_repo_path)
        mock_auditor_class.assert_called_once_with(self.random_repo_path)

    @patch('skills.repo_health_guardian.RepoMonitor')
    @patch('skills.repo_health_guardian.RepoAuditor')
    def test_check_health_and_audit_success(self, mock_auditor_class, mock_monitor_class):
        expected_status = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_audit = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_monitor = mock_monitor_class.return_value
        mock_monitor.check_status.return_value = expected_status

        mock_auditor = mock_auditor_class.return_value
        mock_auditor.audit.return_value = expected_audit

        guardian = RepoHealthGuardian(self.random_repo_path)
        result = guardian.check_health_and_audit()

        self.assertIn("status", result)
        self.assertIn("audit", result)
        self.assertEqual(result["status"], expected_status)
        self.assertEqual(result["audit"], expected_audit)
        mock_monitor.check_status.assert_called_once()
        mock_auditor.audit.assert_called_once()

    @patch('skills.repo_health_guardian.RepoMonitor')
    @patch('skills.repo_health_guardian.RepoAuditor')
    def test_check_health_and_audit_handles_exceptions(self, mock_auditor_class, mock_monitor_class):
        mock_monitor = mock_monitor_class.return_value
        random_error_message = uuid.uuid4().hex
        mock_monitor.check_status.side_effect = Exception(random_error_message)

        guardian = RepoHealthGuardian(self.random_repo_path)
        
        with self.assertRaises(Exception) as context:
            guardian.check_health_and_audit()
        
        self.assertIn(random_error_message, str(context.exception))

    @patch('skills.repo_health_guardian.RepoMonitor')
    @patch('skills.repo_health_guardian.RepoAuditor')
    def test_run_preventive_maintenance_success(self, mock_auditor_class, mock_monitor_class):
        expected_issues = [uuid.uuid4().hex, uuid.uuid4().hex