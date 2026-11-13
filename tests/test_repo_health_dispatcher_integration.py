import os
import unittest
import uuid
import tempfile
from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.dispatcher = RepoHealthDispatcher(self.repo_path)
        
        self.random_title = f"incident_{uuid.uuid4().hex[:8]}"
        self.random_value = f"metric_val_{uuid.uuid4().hex[:8]}"
        self.report_filename = f"report_{uuid.uuid4().hex[:8]}.json"
        self.file_path = os.path.join(self.repo_path, self.report_filename)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dispatch_health_and_notify_integration(self):
        result = self.dispatcher.dispatch_health_and_notify(self.file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            f"Интеграционный сбой: файл отчета {self.file_path} не был создан реальными навыками."
        )

    def test_process_stream_and_dispatch_integration(self):
        stream_data = f'{{"metric": "{uuid.uuid4().hex}"}}'
        
        result = self.dispatcher.process_stream_and_dispatch(stream_data, self.file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            f"Интеграционный сбой: файл из стрима {self.file_path} не был сгенерирован."
        )

    def test_check_and_notify_critical_integration(self):
        result = self.dispatcher.check_and_notify_critical(
            self.random_title, 
            self.random_value, 
            self.file_path
        )
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            f"Интеграционный сбой: критический виджет не записан по пути {self.file_path}."
        )
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(
                self.random_value, 
                content, 
                "Интеграционный сбой: случайное значение метрики не найдено в результирующем файле."
            )

    def test_dispatch_default_integration(self):
        default_report_path = os.path.join(self.repo_path, "report.json")
        result = self.dispatcher.dispatch()
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(default_report_path),
            "Интеграционный сбой: дефолтный метод dispatch() не создал 'report.json'."
        )


if __name__ == "__main__":
    unittest.main()