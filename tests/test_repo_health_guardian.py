import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.repo_health_guardian import RepoHealthGuardian

class TestRepoHealthGuardian(unittest.TestCase):
    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.random_status_key = uuid.uuid4().hex
        self.random_status_value = uuid.uuid4().hex
        self.random_issue = uuid.uuid4().hex
        self.random_structure_key = uuid.uuid4().hex
        self.random_structure_val = uuid.uuid4().hex

    def test_init_and_public_signatures(self):
        guardian = RepoHealthGuardian(self.random_repo_path)
        self.assertEqual(guardian.repo_path, self.random_repo_path)
        self.assertIsNotNone(guardian.monitor)
        self.assertIsNotNone(guardian.auditor)

    def test_check_health_and_audit(self):
        guardian = RepoHealthGuardian(self.random_repo_path)
        
        mock_status = {self.random_status_key: self.random_status_value}
        mock_audit = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(guardian.monitor, 'check_status', return_value=mock_status) as mock_check, \
             patch.object(guardian.auditor, 'audit', return_value=mock_audit) as mock_audit_method:
            
            result = guardian.check_health_and_audit()
            
            mock_check.assert_called_once()
            mock_audit_method.assert_called_once()
            
            self.assertIn("status", result)
            self.assertIn("audit", result)
            self.assertEqual(result["status"], mock_status)
            self.assertEqual(result["audit"], mock_audit)
            self.assertEqual(result["status"][self.random_status_key], self.random_status_value)

    def test_run_preventive_maintenance(self):
        guardian = RepoHealthGuardian(self.random_repo_path)
        
        mock_issues = [self.random_issue, uuid.uuid4().hex]

        with patch.object(guardian.monitor, 'check_status') as mock_check, \
             patch.object(guardian.auditor, 'detect_issues', return_value=mock_issues) as mock_detect:
            
            result = guardian.run_preventive_maintenance()
            
            mock_check.assert_called_once()
            mock_detect.assert_called_once()
            
            self.assertIn("issues_detected", result)
            self.assertIn("action_taken", result)
            self.assertEqual(result["issues_detected"], mock_issues)
            self.assertTrue(result["action_taken"])
            self.assertIn(self.random_issue, result["issues_detected"])

    def test_analyze_repo_structure(self):
        guardian = RepoHealthGuardian(self.random_repo_path)
        
        mock_structure = {self.random_structure_key: self.random_structure_val}

        with patch.object(guardian.auditor, 'analyze_structure', return_value=mock_structure) as mock_analyze:
            result = guardian.analyze_repo_structure()
            
            mock_analyze.assert_called_once()
            self.assertEqual(result, mock_structure)
            self.assertEqual(result[self.random_structure_key], self.random_structure_val)

if __name__ == '__main__':
    unittest.main()