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
        
        self.random_filename = f"report_{uuid.uuid4().hex[:8]}.json"
        self.file_path = os.path.join(self.repo_path, self.random_filename)
        
        self.random_title = f"Metric_{uuid.uuid4().hex[:6]}"
        self.random_value = random.randint(100, 9999)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dispatch_health_and_notify_integration(self):
        result = self.dispatcher.dispatch_health_and_notify(self.file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            f"Файл отчета {self.file_path} должен быть создан реальным дашбордом."
        )

    def test_process_stream_and_dispatch_integration(self):
        stream_data = f'{{"metric_id": "{uuid.uuid4()}", "value": {random.random()}}}'
        
        result = self.dispatcher.process_stream_and_dispatch(stream_data, self.file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            "Файл отчета должен быть экспортирован после обработки потока данных."
        )
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0, "Экспортированный файл отчета не должен быть пустым.")

    def test_check_and_notify_critical_integration(self):
        result = self.dispatcher.check_and_notify_critical(
            self.random_title, 
            self.random_value, 
            self.file_path
        )
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            "Критический виджет должен записать данные в целевой файл."
        )
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            widget_content = f.read()
            self.assertIn(self.random_title, widget_content, "Случайный заголовок метрики должен присутствовать в виджете.")
            self.assertIn(str(self.random_value), widget_content, "Случайное значение метрики должно присутствовать в виджете.")

    def test_dispatch_default_path_integration(self):
        default_report_path = os.path.join(self.repo_path, "report.json")
        
        result = self.dispatcher.dispatch()
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(default_report_path),
            "Метод dispatch должен создавать report.json по умолчанию в корне репозитория."
        )


if __name__ == "__main__":
    unittest.main()