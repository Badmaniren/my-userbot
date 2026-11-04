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

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dispatch_health_and_notify_integration(self):
        unique_filename = f"report_{uuid.uuid4().hex}.json"
        file_path = os.path.join(self.repo_path, unique_filename)

        result = self.dispatcher.dispatch_health_and_notify(file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path), "Файл отчета должен быть создан дашбордом и использован нотификатором.")

    def test_process_stream_and_dispatch_integration(self):
        unique_filename = f"stream_report_{uuid.uuid4().hex}.json"
        file_path = os.path.join(self.repo_path, unique_filename)
        
        stream_data = f"event_id_{uuid.uuid4().hex}: metric_value_{random.randint(1000, 9999)}"

        result = self.dispatcher.process_stream_and_dispatch(stream_data, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path), "Стрим должен обработаться дашбордом и экспортироваться для рассылки.")

    def test_check_and_notify_critical_integration(self):
        title = f"Critical_Widget_{uuid.uuid4().hex[:8]}"
        value = random.randint(100, 999)
        unique_filename = f"critical_{uuid.uuid4().hex}.txt"
        file_path = os.path.join(self.repo_path, unique_filename)

        result = self.dispatcher.check_and_notify_critical(title, value, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path), "Виджет должен быть отрендерен и записан в файл перед нотификацией.")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(str(value), content)

    def test_dispatch_default_integration(self):
        result = self.dispatcher.dispatch()
        self.assertIsInstance(result, bool)
        expected_default_report = os.path.join(self.repo_path, "report.json")
        self.assertTrue(os.path.exists(expected_default_report), "Дефолтный метод dispatch должен создавать report.json в корне репозитория.")


if __name__ == "__main__":
    unittest.main()