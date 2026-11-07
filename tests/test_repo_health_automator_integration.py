import unittest
import tempfile
import shutil
import os
import uuid
import random
import io
from skills.repo_health_automator import RepoHealthAutomator

class TestRepoHealthAutomatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.random_id = str(uuid.uuid4())
        self.random_metric_value = random.randint(100, 999)
        
        marker_file = os.path.join(self.repo_path, f"health_marker_{self.random_id}.txt")
        with open(marker_file, "w", encoding="utf-8") as f:
            f.write(f"Diagnostic metric baseline: {self.random_metric_value}\n")

        self.automator = RepoHealthAutomator(self.repo_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_automate_health_and_maintenance_integration(self):
        result = self.automator.automate_health_and_maintenance()
        
        self.assertIsInstance(result, dict, "Результат должен быть словарем")
        self.assertIn("monitor_status", result)
        self.assertIn("health_audit", result)
        self.assertIn("preventive_maintenance", result)
        
        self.assertIsNotNone(result["monitor_status"])
        self.assertIsNotNone(result["health_audit"])
        self.assertIsNotNone(result["preventive_maintenance"])

    def test_process_stream_and_automate_integration(self):
        stream_content = f"Stream input payload ID: {self.random_id} with weight {self.random_metric_value}"
        stream = io.StringIO(stream_content)
        
        result = self.automator.process_stream_and_automate(stream)
        
        self.assertIsInstance(result, dict, "Результат обработки потока должен быть словарем")
        self.assertIn("monitor_status", result)
        self.assertIn("health_audit", result)
        self.assertIn("preventive_maintenance", result)

    def test_run_and_aliases_integration(self):
        run_result = self.automator.run()
        check_result = self.automator.automate_health_check()
        
        self.assertIsInstance(run_result, dict)
        self.assertIsInstance(check_result, dict)
        
        self.assertEqual(run_result.keys(), check_result.keys())

if __name__ == "__main__":
    unittest.main()