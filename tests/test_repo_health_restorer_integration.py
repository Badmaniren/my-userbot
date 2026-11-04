import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_health_restorer import RepoHealthRestorer

class TestRepoHealthRestorerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Architect Test'")
        os.system(f"git -C {self.test_dir} config user.email 'architect@test.com'")
        
        self.restorer = RepoHealthRestorer(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_restore_and_protect_integration(self):
        unique_file = f"file_{uuid.uuid4().hex}.txt"
        file_path = os.path.join(self.test_dir, unique_file)
        random_content = f"content_{random.randint(1000, 9999)}"
        
        with open(file_path, "w") as f:
            f.write(random_content)
            
        os.system(f"git -C {self.test_dir} add {unique_file}")
        os.system(f"git -C {self.test_dir} commit -m 'Initial commit {uuid.uuid4().hex}'")

        result = self.restorer.restore_and_protect()

        self.assertIsInstance(result, dict)
        self.assertIn("recovery_status", result)
        self.assertIn("maintenance_report", result)
        self.assertIsInstance(result["recovery_status"], bool)
        self.assertIsInstance(result["maintenance_report"], dict)

    def test_comprehensive_health_restoration_integration(self):
        stream_data = f"stream_payload_{uuid.uuid4().hex}"
        
        result = self.restorer.comprehensive_health_restoration(stream_data)

        self.assertIsInstance(result, dict)
        self.assertIn("restored", result)
        self.assertIn("structure_analysis", result)
        self.assertIsInstance(result["restored"], bool)
        self.assertIsInstance(result["structure_analysis"], dict)

    def test_execute_restoration_routine_integration(self):
        dummy_file = os.path.join(self.test_dir, f"dummy_{uuid.uuid4().hex}.py")
        with open(dummy_file, "w") as f:
            f.write(f"print('{uuid.uuid4().hex}')\n")

        status = self.restorer.execute_restoration_routine()

        self.assertIsInstance(status, bool)

if __name__ == "__main__":
    unittest.main()