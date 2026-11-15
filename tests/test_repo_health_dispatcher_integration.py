import os
import shutil
import tempfile
import unittest
import uuid
import random

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.dispatcher = RepoHealthDispatcher(self.test_dir)
        self.unique_id = str(uuid.uuid4())
        self.random_value = random.randint(100, 9999)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors.TrueAny if hasattr(shutil, 'IGNORE_ERRORS') else True)

    def test_dispatch_health_and_notify_integration(self):
        file_name = f"health_report_{self.unique_id}.json"
        file_path = os.path.join(self.test_dir, file_name)

        result = self.dispatcher.dispatch_health_and_notify(file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(file_path),
            f"Integration failure: Exported dashboard file {file_path} was not created."
        )

    def test_process_stream_and_dispatch_integration(self):
        stream_data = f'{{"status": "active", "id": "{self.unique_id}", "metric": {self.random_value}}}'
        file_name = f"stream_report_{self.unique_id}.json"
        file_path = os.path.join(self.test_dir, file_name)

        result = self.dispatcher.process_stream_and_dispatch(stream_data, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(file_path),
            f"Integration failure: Stream processed dashboard file {file_path} was not created."
        )

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertTrue(len(content) > 0, "Exported file content is empty.")

    def test_check_and_notify_critical_integration(self):
        title = f"Critical_Alert_{self.unique_id}"
        file_name = f"critical_{self.unique_id}.log"
        file_path = os.path.join(self.test_dir, file_name)

        result = self.dispatcher.check_and_notify_critical(title, self.random_value, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(file_path),
            f"Integration failure: Critical widget file {file_path} was not created."
        )

        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(title, file_content)

    def test_dispatch_default_integration(self):
        result = self.dispatcher.dispatch()
        expected_path = os.path.join(self.test_dir, "report.json")

        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(expected_path),
            f"Integration failure: Default dispatch report.json was not generated at {expected_path}."
        )


if __name__ == "__main__":
    unittest.main()