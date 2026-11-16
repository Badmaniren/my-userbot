import unittest
import os
import uuid
import random
import tempfile
from skills.repo_health_dispatcher import RepoHealthDispatcher

class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dispatcher = RepoHealthDispatcher(self.test_dir)
        self.unique_id = str(uuid.uuid4())
        self.random_value = random.randint(100, 9999)
        self.file_path = os.path.join(self.test_dir, f"report_{self.unique_id}.json")

    def tearDown(self):
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except OSError:
                pass

    def test_dispatch_health_and_notify_integration(self):
        result = self.dispatcher.dispatch_health_and_notify(self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path), "Dashboard export file must be created during real integration execution")

    def test_process_stream_and_dispatch_integration(self):
        stream_content = f'{{"metric": "{self.unique_id}", "value": {self.random_value}}}'
        result = self.dispatcher.process_stream_and_dispatch(stream_content, self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path), "Stream processing must successfully export the dashboard to the target file")

    def test_check_and_notify_critical_integration(self):
        title = f"CriticalAlert_{self.unique_id}"
        result = self.dispatcher.check_and_notify_critical(title, self.random_value, self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path), "Critical check must render and persist the widget to the file system")
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(title, content, "Rendered widget file must contain the dynamically generated title")

    def test_default_dispatch_integration(self):
        expected_report_path = os.path.join(self.test_dir, "report.json")
        try:
            result = self.dispatcher.dispatch()
            self.assertIsInstance(result, bool)
            self.assertTrue(os.path.exists(expected_report_path), "Default dispatch must generate report.json in the repository path")
        finally:
            if os.path.exists(expected_report_path):
                try:
                    os.remove(expected_report_path)
                except OSError:
                    pass

if __name__ == "__main__":
    unittest.main()