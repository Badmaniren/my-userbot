import unittest
from unittest.mock import patch
import random
import uuid
import string

from skills.repo_health_guardian import RepoHealthGuardian

class TestRepoHealthGuardian(unittest.TestCase):
    def test_guardian_initialization_and_composition(self):
        rand_repo = f"/tmp/repo_{uuid.uuid4().hex}"
        
        with patch("skills.repo_health_guardian.RepoMonitor") as mock_monitor_cls, \
             patch("skills.repo_health_guardian.RepoAuditor") as mock_auditor_cls:
            
            mock_monitor_instance = mock_monitor_cls.return_value
            mock_auditor_instance = mock_auditor_cls.return_value
            
            guardian = RepoHealthGuardian(rand_repo)
            
            mock_monitor_cls.assert_called_once_with(rand_repo)
            mock_auditor_cls.assert_called_once_with(rand_repo)
            
            self.assertEqual(guardian.repo_path, rand_repo)
            self.assertIs(guardian.monitor, mock_monitor_instance)
            self.assertIs(guardian.auditor, mock_auditor_instance)

    def test_check_health_and_audit(self):
        rand_repo = f"/var/git/{uuid.uuid4().hex}"
        rand_status = f"status_{uuid.uuid4().hex}"
        rand_metric_key = f"metric_{uuid.uuid4().hex}"
        rand_metric_val = random.randint(10, 1000)
        
        with patch("skills.repo_health_guardian.RepoMonitor") as mock_monitor_cls, \
             patch("skills.repo_health_guardian.RepoAuditor") as mock_auditor_cls:
            
            mock_monitor = mock_monitor_cls.return_value
            mock_monitor.check_status.return_value = rand_status
            
            mock_auditor = mock_auditor_cls.return_value
            mock_auditor.audit.return_value = {rand_metric_key: rand_metric_val}
            
            guardian = RepoHealthGuardian(rand_repo)
            health_report = guardian.check_health_and_audit()
            
            mock_monitor.check_status.assert_called_once()
            mock_auditor.audit.assert_called_once()
            
            self.assertIn("status", health_report)
            self.assertIn("audit", health_report)
            self.assertEqual(health_report["status"], rand_status)
            self.assertEqual(health_report["audit"][rand_metric_key], rand_metric_val)

    def test_preventive_maintenance_action(self):
        rand_repo = f"/opt/repos/{uuid.uuid4().hex}"
        rand_issue = f"issue_{uuid.uuid4().hex}"
        
        with patch("skills.repo_health_guardian.RepoMonitor") as mock_monitor_cls, \
             patch("skills.repo_health_guardian.RepoAuditor") as mock_auditor_cls:
            
            mock_monitor = mock_monitor_cls.return_value
            mock_monitor.check_status.return_value = f"clean_{uuid.uuid4().hex}"
            
            mock_auditor = mock_auditor_cls.return_value
            mock_auditor.detect_issues.return_value = [rand_issue]
            
            guardian = RepoHealthGuardian(rand_repo)
            result = guardian.run_preventive_maintenance()
            
            mock_monitor.check_status.assert_called_once()
            mock_auditor.detect_issues.assert_called_once()
            
            self.assertIsInstance(result, dict)
            self.assertIn("issues_detected", result)
            self.assertIn(rand_issue, result["issues_detected"])
            self.assertTrue(result["action_taken"])

    def test_guardian_structure_analysis(self):
        rand_repo = f"/home/user/repo_{uuid.uuid4().hex}"
        rand_key = ''.join(random.choices(string.ascii_lowercase, k=8))
        rand_val = ''.join(random.choices(string.ascii_uppercase, k=6))
        
        with patch("skills.repo_health_guardian.RepoMonitor") as mock_monitor_cls, \
             patch("skills.repo_health_guardian.RepoAuditor") as mock_auditor_cls:
            
            mock_auditor = mock_auditor_cls.return_value
            mock_auditor.analyze_structure.return_value = {rand_key: rand_val}
            
            guardian = RepoHealthGuardian(rand_repo)
            structure_data = guardian.analyze_repo_structure()
            
            mock_auditor.analyze_structure.assert_called_once()
            self.assertEqual(structure_data[rand_key], rand_val)