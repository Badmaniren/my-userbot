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
        self.random_tag = str(uuid.uuid4())
        self.report_filename = f"report_{self.random_tag}.json"
        self.file_path = os.path.join(self.test_dir, self.report_filename)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dispatch_health_and_notify_integration(self):
        result = self.dispatcher.dispatch_health_and_notify(self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path), "Интеграционный тест ожидает реального создания файла отчета дашбордом.")

    def test_process_stream_and_dispatch_integration(self):
        random_content = f"metric_id: {uuid.uuid4()} value: {random.randint(100, 999)}"
        result = self.dispatcher.process_stream_and_dispatch(random_content, self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path), "Поток должен быть обработан и экспортирован реальным дашбордом в файл.")

    def test_check_and_notify_critical_integration(self):
        widget_title = f"Critical_Alert_{uuid.uuid4()}"
        widget_value = random.randint(1000, 9999)
        result = self.dispatcher.check_and_notify_critical(widget_title, widget_value, self.file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(self.file_path), "Критический виджет должен записать данные на диск.")
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(str(widget_value), content, "В реальном файле должны присутствовать переданные случайные данные виджета.")

    def test_dispatch_default_integration(self):
        result = self.dispatcher.dispatch()
        default_report_path = os.path.join(self.test_dir, "report.json")
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(default_report_path), "Метод dispatch должен порождать дефолтный отчет в целевой директории репозитория.")


if __name__ == "__main__":
    unittest.main()