import unittest
import uuid
import random
import os
import tempfile
from skills.repo_health_guardian import RepoHealthGuardian

class TestRepoHealthGuardianIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.unique_id = str(uuid.uuid4())
        
        # Создаем минимальную структуру репозитория для реальной работы навыков мониторинга и аудита
        os.makedirs(os.path.join(self.repo_path, ".git"), exist_ok=True)
        self.test_file_name = f"test_file_{self.unique_id}.txt"
        with open(os.path.join(self.repo_path, self.test_file_name), "w") as f:
            f.write(f"random content {random.randint(1, 1000)}")

        self.guardian = RepoHealthGuardian(self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_check_health_and_audit_integration(self):
        result = self.guardian.check_health_and_audit()
        
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("audit", result)
        
        audit_data = result["audit"]
        self.assertIsInstance(audit_data, dict)

    def test_run_preventive_maintenance_integration(self):
        result = self.guardian.run_preventive_maintenance()
        
        self.assertIsInstance(result, dict)
        self.assertIn("issues_detected", result)
        self.assertIn("action_taken", result)
        self.assertTrue(result["action_taken"])
        self.assertIsInstance(result["issues_detected"], (list, dict))

    def test_analyze_repo_structure_integration(self):
        structure = self.guardian.analyze_repo_structure()
        
        self.assertIsInstance(structure, dict)

if __name__ == "__main__":
    unittest.main()