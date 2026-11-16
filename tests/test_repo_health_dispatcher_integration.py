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
        self.repo_path = self.test_dir
        self.dispatcher = RepoHealthDispatcher(self.repo_path)
        self.random_id = str(uuid.uuid4())
        self.metric_value = random.randint(10, 100)
        self.report_filename = f"report_{self.random_id}.json"
        self.report_path = os.path.join(self.repo_path, self.report_filename)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dispatch_health_and_notify_integration(self):
        result = self.dispatcher.dispatch_health_and_notify(self.report_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.report_path),
            f"Файл отчета {self.report_path} должен быть реально создан в репозитории."
        )

    def test_process_stream_and_dispatch_integration(self):
        stream_content = f'{{"metrics_id": "{self.random_id}", "status": "healthy"}}'
        result = self.dispatcher.process_stream_and_dispatch(stream_content, self.report_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.report_path),
            "Файл отчета из стрима должен быть записан на диск."
        )
        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.random_id, content, "Сгенерированный UUID должен присутствовать в экспортированных данных.")

    def test_check_and_notify_critical_integration(self):
        widget_title = f"Critical Alert {self.random_id}"
        result = self.dispatcher.check_and_notify_critical(widget_title, self.metric_value, self.report_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.report_path),
            "Критический виджет должен физически создать файл отчета."
        )
        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(widget_title, content, "Заголовок виджета с уникальным ID должен быть записан в файл.")


if __name__ == "__main__":
    unittest.main()