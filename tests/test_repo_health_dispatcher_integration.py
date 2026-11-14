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

        self.assertTrue(
            os.path.exists(file_path),
            f"Файл отчета {file_path} должен быть создан реальным дашбордом."
        )
        self.assertIsInstance(result, bool)

    def test_process_stream_and_dispatch_integration(self):
        random_stream_content = f'{{"metric_id": "{uuid.uuid4()}", "value": {random.randint(1, 1000)}}}'
        unique_filename = f"stream_report_{uuid.uuid4().hex}.json"
        file_path = os.path.join(self.repo_path, unique_filename)

        result = self.dispatcher.process_stream_and_dispatch(random_stream_content, file_path)

        self.assertTrue(
            os.path.exists(file_path),
            f"Файл из стрима {file_path} должен быть успешно сгенерирован и экспортирован."
        )
        self.assertIsInstance(result, bool)

    def test_check_and_notify_critical_integration(self):
        random_title = f"Critical_Incident_{uuid.uuid4().hex[:8]}"
        random_value = random.randint(90, 100)
        unique_filename = f"critical_{uuid.uuid4().hex}.log"
        file_path = os.path.join(self.repo_path, unique_filename)

        result = self.dispatcher.check_and_notify_critical(random_title, random_value, file_path)

        self.assertTrue(
            os.path.exists(file_path),
            f"Критический виджет должен быть записан на диск по пути {file_path}."
        )
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(random_title, content, "Записанный файл должен содержать переданный заголовок инцидента.")

        self.assertIsInstance(result, bool)

    def test_dispatch_default_integration(self):
        default_report_path = os.path.join(self.repo_path, "report.json")

        result = self.dispatcher.dispatch()

        self.assertTrue(
            os.path.exists(default_report_path),
            "Метод dispatch() должен создавать стандартный файл report.json в корне репозитория."
        )
        self.assertIsInstance(result, bool)


if __name__ == "__main__":
    unittest.main()