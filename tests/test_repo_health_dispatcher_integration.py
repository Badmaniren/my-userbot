import os
import shutil
import tempfile
import unittest
import uuid
from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dispatcher = RepoHealthDispatcher(self.test_dir)
        self.unique_id = str(uuid.uuid4())
        self.report_filename = f"report_{self.unique_id}.json"
        self.file_path = os.path.join(self.test_dir, self.report_filename)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dispatch_health_and_notify_integration(self):
        result = self.dispatcher.dispatch_health_and_notify(self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path))

    def test_process_stream_and_dispatch_integration(self):
        stream_data = f'{{"status": "healthy", "id": "{self.unique_id}"}}'
        result = self.dispatcher.process_stream_and_dispatch(stream_data, self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path))
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.unique_id, content)

    def test_check_and_notify_critical_integration(self):
        title = f"Critical Alert {self.unique_id}"
        value = uuid.uuid4().hex
        result = self.dispatcher.check_and_notify_critical(title, value, self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path))
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(title, content)
            self.assertIn(str(value), content)

    def test_dispatch_integration(self):
        result = self.dispatcher.dispatch()
        self.assertIsInstance(result, bool)
        default_report_path = os.path.join(self.test_dir, "report.json")
        self.assertTrue(os.path.exists(default_report_path))


if __name__ == "__main__":
    unittest.main()