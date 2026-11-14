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
        self.guardian = RepoHealthGuardian(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_check_health_and_audit_integration(self):
        dummy_file_name = f"test_file_{self.random_id}.txt"
        dummy_file_path = os.path.join(self.test_dir, dummy_file_name)
        
        random_content = f"content_{random.randint(1000, 9999)}"
        with open(dummy_file_path, "w", encoding="utf-8") as f:
            f.write(random_content)

        result = self.guardian.check_health_and_audit()

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("audit", result)
        
        monitor_status = result["status"]
        audit_data = result["audit"]
        
        self.assertIsNotNone(monitor_status)
        self.assertIsNotNone(audit_data)

    def test_run_preventive_maintenance_integration(self):
        random_subfolder = os.path.join(self.test_dir, f"dir_{self.random_id}")
        os.makedirs(random_subfolder, exist_ok=True)
        
        nested_file = os.path.join(random_subfolder, "nested.json")
        with open(nested_file, "w", encoding="utf-8") as f:
            f.write('{"status": "active"}')

        result = self.guardian.run_preventive_maintenance()

        self.assertIsInstance(result, dict)
        self.assertIn("issues_detected", result)
        self.assertIn("action_taken", result)
        self.assertTrue(result["action_taken"])

    def test_analyze_repo_structure_integration(self):
        expected_token = f"token_{self.random_id}"
        target_file = os.path.join(self.test_dir, f"{expected_token}.log")
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(expected_token)

        structure_analysis = self.guardian.analyze_repo_structure()

        self.assertIsInstance(structure_analysis, dict)
        
        structure_str = str(structure_analysis)
        self.assertTrue(
            len(structure_str) > 0, 
            "Structural analysis must return valid non-empty metadata."
        )

if __name__ == "__main__":
    unittest.main()