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
        self.assertTrue(os.path.exists(file_path), f"Файл отчета не был создан: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0, "Созданный файл отчета пуст")

    def test_process_stream_and_dispatch_integration(self):
        unique_filename = f"stream_report_{uuid.uuid4().hex}.json"
        file_path = os.path.join(self.repo_path, unique_filename)
        
        random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        random_metric_value = random.randint(100, 9999)
        stream_data = f'{{"title": "{random_metric_name}", "value": {random_metric_value}}}'
        
        result = self.dispatcher.process_stream_and_dispatch(stream_data, file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path), f"Файл стрим-отчета не был создан: {file_path}")

    def test_check_and_notify_critical_integration(self):
        unique_filename = f"critical_{uuid.uuid4().hex}.txt"
        file_path = os.path.join(self.repo_path, unique_filename)
        
        critical_title = f"CRITICAL_INCIDENT_{uuid.uuid4().hex[:6]}"
        critical_value = random.uniform(90.0, 100.0)
        
        result = self.dispatcher.check_and_notify_critical(critical_title, critical_value, file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path), f"Критический виджет не записан в файл: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(critical_title, file_content)

    def test_dispatch_default_integration(self):
        result = self.dispatcher.dispatch()
        
        self.assertIsInstance(result, bool)
        default_report_path = os.path.join(self.repo_path, "report.json")
        self.assertTrue(os.path.exists(default_report_path), "Дефолтный отчет не сгенерирован методом dispatch()")

if __name__ == "__main__":
    unittest.main()