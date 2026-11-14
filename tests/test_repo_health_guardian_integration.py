import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_health_guardian import RepoHealthGuardian
from skills.repo_monitor import RepoMonitor
from skills.repo_auditor import RepoAuditor

class TestRepoHealthGuardianIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.random_id = str(uuid.uuid4())
        self.marker_file = os.path.join(self.test_dir, f"health_marker_{self.random_id}.txt")
        
        with open(self.marker_file, "w", encoding="utf-8") as f:
            f.write(f"integration test data {random.randint(1000, 9999)}")
            
        self.guardian = RepoHealthGuardian(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_check_health_and_audit_integration(self):
        result = self.guardian.check_health_and_audit()
        
        self.assertIn("status", result)
        self.assertIn("audit", result)
        
        monitor_instance = RepoMonitor(self.test_dir)
        expected_status = monitor_instance.check_status()
        self.assertEqual(result["status"], expected_status)
        
        auditor_instance = RepoAuditor(self.test_dir)
        expected_audit = auditor_instance.audit()
        self.assertEqual(result["audit"], expected_audit)

    def test_run_preventive_maintenance_integration(self):
        result = self.guardian.run_preventive_maintenance()
        
        self.assertIn("issues_detected", result)
        self.assertIn("action_taken", result)
        self.assertTrue(result["action_taken"])
        
        auditor_instance = RepoAuditor(self.test_dir)
        expected_issues = auditor_instance.detect_issues()
        self.assertEqual(result["issues_detected"], expected_issues)

    def test_analyze_repo_structure_integration(self):
        result = self.guardian.analyze_repo_structure()
        
        auditor_instance = RepoAuditor(self.test_dir)
        expected_structure = auditor_instance.analyze_structure()
        self.assertEqual(result, expected_structure)

if __name__ == "__main__":
    unittest.main()