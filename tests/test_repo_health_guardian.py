import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.repo_health_guardian import RepoHealthGuardian

class TestRepoHealthGuardian(unittest.TestCase):
    def setUp(self):
        self.rand_path = f"/tmp/repo_{uuid.uuid4().hex[:8]}"
        self.guardian = RepoHealthGuardian(self.repo_path) if hasattr(self, 'repo_path') else RepoHealthGuardian(self.rand_path)

    def test_init_sets_paths_and_dependencies(self):
        custom_path = f"/var/git/{uuid.uuid4().hex}"
        with patch("skills.repo_health_guardian.RepoMonitor") as mock_monitor_cls, \
             patch("skills.repo_health_guardian.RepoAuditor") as mock_auditor_cls:
            
            guardian = RepoHealthGuardian(custom_path)
            self.assertEqual(guardian.repo_path, custom_path)
            mock_monitor_cls.assert_called_once_with(custom_path)
            mock_auditor_cls.assert_called_once_with(custom_path)

    def test_check_health_and_audit_returns_correct_structure(self):
        expected_status = {uuid.uuid4().hex: ''.join(random.choices(string.ascii_letters, k=5))}
        expected_audit = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(self.guardian.monitor, 'check_status', return_value=expected_status) as mock_status, \
             patch.object(self.guardian.auditor, 'audit', return_value=expected_audit) as mock_audit:
            
            result = self.guardian.check_health_and_audit()
            
            mock_status.assert_called_once()
            mock_audit.assert_called_once()
            self.assertIn("status", result)
            self.assertIn("audit", result)
            self.assertEqual(result["status"], expected_status)
            self.assertEqual(result["audit"], expected_audit)

    def test_run_preventive_maintenance_triggers_audit_and_returns_issues(self):
        rand_issue = uuid.uuid4().hex
        expected_issues = [rand_issue]

        with patch.object(self.guardian.monitor, 'check_status') as mock_status, \
             patch.object(self.guardian.auditor, 'detect_issues', return_value=expected_issues) as mock_detect:
            
            result = self.guardian.run_preventive_maintenance()
            
            mock_status.assert_called_once()
            mock_detect.assert_called_once()
            self.assertIn("issues_detected", result)
            self.assertIn("action_taken", result)
            self.assertEqual(result["issues_detected"], expected_issues)
            self.assertTrue(result["action_taken"])

    def test_analyze_repo_structure_delegates_to_auditor(self):
        random_key = uuid.uuid4().hex
        random_val = random.randint(500, 1000)
        expected_structure = {random_key: random_val}

        with patch.object(self.guardian.auditor, 'analyze_structure', return_value=expected_structure) as mock_analyze:
            result = self.guardian.analyze_repo_structure()
            
            mock_analyze.assert_called_once()
            self.assertEqual(result, expected_structure)

    def test_audit_signal_handling_no_bare_excepts(self):
        with patch.object(self.guardian.monitor, 'check_status', side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(Exception):
                self.guardian.check_health_and_audit()

if __name__ == "__main__":
    unittest.main()