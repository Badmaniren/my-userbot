import unittest
import uuid
import random
import tempfile
import shutil
from pathlib import Path
from skills.repo_health_guardian import RepoHealthGuardian

class TestRepoHealthGuardianIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.guardian = RepoHealthGuardian(self.repo_path)
        
        self.random_id = str(uuid.uuid4())
        self.random_value = random.randint(1000, 9999)
        
        test_file = Path(self.repo_path) / f"test_file_{self.random_id}.txt"
        test_file.write_text(f"integrity check value: {self.random_value}")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_check_health_and_audit_integration(self):
        result = self.guardian.check_health_and_audit()
        
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("audit", result)
        self.assertIsNotNone(result["status"])
        self.assertIsNotNone(result["audit"])

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
        
        structure_str = str(structure)
        self.assertIn(self.random_id, structure_str)

if __name__ == "__main__":
    unittest.main()