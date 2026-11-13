import io
import os
import random
import shutil
import subprocess
import tempfile
import unittest
import uuid

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.temp_dir, f"repo_{uuid.uuid4().hex}")
        os.makedirs(self.repo_path, exist_ok=True)

        try:
            subprocess.run(["git", "init"], cwd=self.repo_path, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.name", "Test Architect"], cwd=self.repo_path, capture_output=True, check=True)
            subprocess.run(["git", "config", "user.email", "architect@test.local"], cwd=self.repo_path, capture_output=True, check=True)
        except Exception:
            pass

        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dispatch_default_creates_report_file(self):
        expected_report_path = os.path.join(self.repo_path, "report.json")
        result = self.dispatcher.dispatch()

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(expected_report_path))

    def test_dispatch_health_and_notify_custom_path(self):
        filename = f"health_report_{uuid.uuid4().hex}.json"
        target_path = os.path.join(self.repo_path, filename)

        result = self.dispatcher.dispatch_health_and_notify(target_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(target_path))

    def test_process_stream_and_dispatch_with_string_stream(self):
        random_metric_name = f"metric_{uuid.uuid4().hex}"
        random_value = random.randint(100, 9999)
        stream_content = f'{{"metric": "{random_metric_name}", "value": {random_value}}}'
        filename = f"stream_report_{uuid.uuid4().hex}.json"
        file_path = os.path.join(self.repo_path, filename)

        result = self.dispatcher.process_stream_and_dispatch(stream_content, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path))

    def test_process_stream_and_dispatch_with_bytes_stream(self):
        random_metric_name = f"metric_{uuid.uuid4().hex}"
        random_value = random.randint(1, 500)
        raw_bytes = io.BytesIO(f'{{"metric": "{random_metric_name}", "value": {random_value}}}'.encode("utf-8"))
        filename = f"stream_bytes_report_{uuid.uuid4().hex}.json"
        file_path = os.path.join(self.repo_path, filename)

        result = self.dispatcher.process_stream_and_dispatch(raw_bytes, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path))

    def test_check_and_notify_critical_writes_widget_and_notifies(self):
        random_title = f"CRITICAL_INCIDENT_{uuid.uuid4().hex}"
        random_value = random.uniform(85.5, 99.9)
        filename = f"critical_{uuid.uuid4().hex}.widget"
        file_path = os.path.join(self.repo_path, filename)

        result = self.dispatcher.check_and_notify_critical(random_title, random_value, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertTrue(len(written_content) > 0)


if __name__ == "__main__":
    unittest.main()