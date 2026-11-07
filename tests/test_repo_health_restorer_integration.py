import unittest
import tempfile
import shutil
import os
import uuid
import random
from io import BytesIO
from skills.repo_health_restorer import RepoHealthRestoreras ArchitectureRestorer

class TestRepoHealthRestorerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.restorer = ArchitectureRestorer(self.test_dir)
        self.random_token = str(uuid.uuid4())

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_restore_and_protect_integration(self):
        result = self.restorer.restore_and_protect()
        self.assertIsInstance(result, dict)
        self.assertIn("recovery_status", result)
        self.assertIn("maintenance_report", result)
        self.assertIsInstance(result["recovery_status"], bool)
        self.assertIsInstance(result["maintenance_report"], dict)

    def test_comprehensive_health_restoration_integration(self):
        payload = f"test_data_{self.random_token}_{random.randint(1000, 9999)}"
        result = self.restorer.comprehensive_health_restoration(payload)
        self.assertIsInstance(result, dict)
        self.assertIn("restored", result)
        self.assertIn("structure_analysis", result)
        self.assertIsInstance(result["restored"], bool)
        self.assertIsInstance(result["structure_analysis"], dict)

    def test_comprehensive_health_restoration_stream_integration(self):
        payload = f"stream_data_{self.random_token}_{random.randint(1000, 9999)}"
        stream = BytesIO(payload.encode("utf-8"))
        result = self.restorer.comprehensive_health_restoration(stream)
        self.assertIsInstance(result, dict)
        self.assertIn("restored", result)
        self.assertIn("structure_analysis", result)
        self.assertIsInstance(result["restored"], bool)

    def test_execute_restoration_routine_integration(self):
        status = self.restorer.execute_restoration_routine()
        self.assertIsInstance(status, bool)

if __name__ == "__main__":
    unittest.main()