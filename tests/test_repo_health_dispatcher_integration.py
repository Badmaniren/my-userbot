import os
import random
import tempfile
import unittest
import uuid

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = os.path.join(self.temp_dir.name, f"repo_{uuid.uuid4().hex}")
        os.makedirs(self.repo_path, exist_ok=True)
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dispatch_health_and_notify_creates_file_and_notifies(self):
        file_name = f"health_report_{uuid.uuid4().hex}.json"
        file_path = os.path.join(self.temp_dir.name, file_name)

        result = self.dispatcher.dispatch_health_and_notify(file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path))

    def test_process_stream_and_dispatch_with_string_stream(self):
        random_stream_data = f"stream_metric_{uuid.uuid4().hex}_val_{random.randint(1000, 9999)}"
        file_name = f"stream_export_{uuid.uuid4().hex}.json"
        file_path = os.path.join(self.temp_dir.name, file_name)

        result = self.dispatcher.process_stream_and_dispatch(random_stream_data, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path))

    def test_check_and_notify_critical_writes_widget_content(self):
        unique_title = f"CRITICAL_INCIDENT_{uuid.uuid4().hex[:8]}"
        unique_value = random.randint(5000, 9999)
        file_name = f"critical_widget_{uuid.uuid4().hex}.txt"
        file_path = os.path.join(self.temp_dir.name, file_name)

        result = self.dispatcher.check_and_notify_critical(unique_title, unique_value, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(str(unique_title), content)

    def test_dispatch_default_report_location(self):
        expected_default_report = os.path.join(self.repo_path, "report.json")

        result = self.dispatcher.dispatch()

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(expected_default_report))


if __name__ == "__main__":
    unittest.main()