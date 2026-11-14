import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
from skills.repo_health_guardian import RepoHealthGuardian

class TestRepoHealthGuardian(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.guardian = RepoHealthGuardian(self.repo_path)

    @patch('skills.repo_health_guardian.RepoMonitor')
    @patch('skills.repo_health_guardian.RepoAuditor')
    def test_check_health_and_audit_success(self, mock_auditor_class, mock_monitor_class):
        mock_monitor_instance = mock_monitor_class.return_value
        mock_auditor_instance = mock_auditor_class.return_value

        expected_status_key = uuid.uuid4().hex
        expected_status_val = uuid.uuid4().hex
        expected_audit_key = uuid.uuid4().hex
        expected_audit_val = uuid.uuid4().hex

        mock_monitor_instance.check_status.return_value = {expected_status_key: expected_status_val}
        mock_auditor_instance.audit.return_value = {expected_audit_key: expected_audit_val}

        guardian = RepoHealthGuardian(self.repo_path)
        result = guardian.check_health_and_audit()

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("audit", result)
        self.assertEqual(result["status"][expected_status_key], expected_status_val)
        self.assertEqual(result["audit"][expected_audit_key], expected_audit_val)

    @patch('skills.repo_health_guardian.RepoMonitor')
    @patch('skills.repo_health_guardian.RepoAuditor')
    def test_check_health_and_audit_error_handling(self, mock_auditor_class, mock_monitor_class):
        mock_monitor_instance = mock_monitor_class.return_value
        err_msg = uuid.uuid4().hex
        mock_monitor_instance.check_status.side_effect = Exception(err_msg)

        guardian = RepoHealthGuardian(self.repo_path)
        with self.assertRaises(Exception) as ctx:
            guardian.check_health_and_audit()
        self.assertIn(err_msg, str(ctx.exception))

    @patch('skills.repo_health_guardian.RepoMonitor')
    @patch('skills.repo_health_guardian.RepoAuditor')
    def test_run_preventive_maintenance_success(self, mock_auditor_class, mock_monitor_class):
        mock_monitor_instance = mock_monitor_class.return_value
        mock_auditor_instance = mock_auditor_class.return_value

        issue_item = uuid.uuid4().hex
        mock_auditor_instance.detect_issues.return_value = [issue_item]

        guardian = RepoHealthGuardian(self.repo_path)
        result = guardian.run_preventive_maintenance()

        self.assertIsInstance(result, dict)
        self.assertIn("issues_detected", result)
        self.assertIn("action_taken", result)
        self.assertEqual(result["issues_detected"], [issue_item])
        self.assertTrue(result["action_taken"])

    @patch('skills.repo_health_guardian.RepoAuditor')
    def test_analyze_repo_structure_success(self, mock_auditor_class):
        mock_auditor_instance = mock_auditor_class.return_value
        structure_key = uuid.uuid4().hex
        structure_val = uuid.uuid4().hex
        mock_auditor_instance.analyze_structure.return_value = {structure_key: structure_val}

        guardian = RepoHealthGuardian(self.repo_path)
        result = guardian.analyze_repo_structure()

        self.assertIsInstance(result, dict)
        self.assertEqual(result[structure_key], structure_val)

    @patch('skills.repo_health_guardian.RepoAuditor')
    def test_analyze_repo_structure_error_propagation(self, mock_auditor_class):
        mock_auditor_instance = mock_auditor_class.return_value
        error_msg = uuid.uuid4().hex
        mock_auditor_instance.analyze_structure.side_effect = RuntimeError(error_msg)

        guardian = RepoHealthGuardian(self.repo_path)
        with self.assertRaises(RuntimeError) as ctx:
            guardian.analyze_repo_structure()
        self.assertIn(error_msg, str(ctx.exception))

if __name__ == '__main__':
    unittest.main()