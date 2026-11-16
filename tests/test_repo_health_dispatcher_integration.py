import os
import shutil
import unittest
import uuid
import random
from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath(f"test_repo_env_{uuid.uuid4().hex}")
        os.makedirs(self.test_dir, exist_ok=True)
        self.dispatcher = RepoHealthDispatcher(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dispatch_health_and_notify_integration(self):
        unique_filename = f"report_{uuid.uuid4().hex}.json"
        file_path = os.path.join(self.test_dir, unique_filename)
        
        result = self.dispatcher.dispatch_health_and_notify(file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path), "Файл отчета должен быть реально создан в файловой системе.")

    def test_process_stream_and_dispatch_integration(self):
        stream_content = f"metrics_stream_data_{uuid.uuid4().hex}"
        unique_filename = f"stream_report_{uuid.uuid4().hex}.json"
        file_path = os.path.join(self.test_dir, unique_filename)

        result = self.dispatcher.process_stream_and_dispatch(stream_content, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path), "Файл отчета из стрима должен быть записан на диск.")

    def test_check_and_notify_critical_integration(self):
        widget_title = f"Critical_Metric_{uuid.uuid4().hex}"
        widget_value = random.randint(100, 9999)
        unique_filename = f"critical_{uuid.uuid4().hex}.txt"
        file_path = os.path.join(self.test_dir, "widgets", unique_filename)

        result = self.dispatcher.check_and_notify_critical(widget_title, widget_value, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path), "Критический виджет должен создать файл отчета.")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(widget_title, content, "Содержимое файла должно содержать переданный заголовок.")
            self.assertIn(str(widget_value), content, "Содержимое файла должно содержать переданное числовое значение.")

    def test_default_dispatch_integration(self):
        result = self.dispatcher.dispatch()
        
        expected_report_path = os.path.join(self.test_dir, "report.json")
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(expected_report_path), "Дефолтный метод dispatch должен создавать report.json.")


if __name__ == "__main__":
    unittest.main()