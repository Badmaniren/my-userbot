import unittest
import os
import tempfile
import uuid
import random
from skills.repo_health_dispatcher import RepoHealthDispatcher

class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.dispatcher = RepoHealthDispatcher(self.repo_path)
        
        self.random_id = str(uuid.uuid4())
        self.random_metric_value = random.randint(100, 9999)
        self.report_filename = f"report_{self.random_id}.json"
        self.file_path = os.path.join(self.repo_path, self.report_filename)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dispatch_health_and_notify_integration(self):
        result = self.dispatcher.dispatch_health_and_notify(self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path))

    def test_process_stream_and_dispatch_integration(self):
        stream_content = f'{{"metric_id": "{self.random_id}", "value": {self.random_metric_value}}}'
        result = self.dispatcher.process_stream_and_dispatch(stream_content, self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path))
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.random_id, content)

    def test_check_and_notify_critical_integration(self):
        title = f"Critical_Alert_{self.random_id}"
        result = self.dispatcher.check_and_notify_critical(title, self.random_metric_value, self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path))
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(title, content)
            self.assertIn(str(self.random_metric_value), content)

    def test_dispatch_default_path_integration(self):
        result = self.dispatcher.dispatch()
        self.assertIsInstance(result, bool)
        default_report_path = os.path.join(self.repo_path, "report.json")
        self.assertTrue(os.path.exists(default_report_path))

if __name__ == "__main__":
    unittest.main()