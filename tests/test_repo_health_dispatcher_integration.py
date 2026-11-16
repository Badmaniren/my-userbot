import unittest
import os
import tempfile
import uuid
import random
from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dispatcher = RepoHealthDispatcher(self.test_dir)
        self.unique_id = str(uuid.uuid4())
        self.report_file_name = f"report_{self.unique_id}.json"
        self.file_path = os.path.join(self.test_dir, self.report_file_name)

    def tearDown(self):
        if os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except OSError:
                pass
        try:
            os.rmdir(self.test_dir)
        except OSError:
            pass

    def test_dispatch_health_and_notify_integration(self):
        result = self.dispatcher.dispatch_health_and_notify(self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path))

    def test_process_stream_and_dispatch_integration(self):
        stream_content = f'{{"status": "healthy", "metric_id": "{self.unique_id}", "value": {random.randint(1, 1000)}}}'
        result = self.dispatcher.process_stream_and_dispatch(stream_content, self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path))
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.unique_id, content)

    def test_check_and_notify_critical_integration(self):
        widget_title = f"Critical Alert {self.unique_id}"
        widget_value = random.randint(9000, 99999)
        result = self.dispatcher.check_and_notify_critical(widget_title, widget_value, self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path))
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(widget_title, content)
            self.assertIn(str(widget_value), content)

    def test_dispatch_default_path_integration(self):
        expected_default_path = os.path.join(self.test_dir, "report.json")
        try:
            result = self.dispatcher.dispatch()
            self.assertIsInstance(result, bool)
            self.assertTrue(os.path.exists(expected_default_path))
        finally:
            if os.path.exists(expected_default_path):
                os.remove(expected_default_path)


if __name__ == "__main__":