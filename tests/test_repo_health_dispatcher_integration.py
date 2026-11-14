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
        
        self.random_title = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_value = random.randint(100, 9999)
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
        random_stream_data = f"stream_data_{uuid.uuid4().hex}"
        result = self.dispatcher.process_stream_and_dispatch(random_stream_data, self.file_path)
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            "Интеграционный сбой: обработка стрима не привела к экспорту файла дашборда."
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
            "Интеграционный сбой: критический виджет не был записан на диск."
        )
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(
                str(self.random_value), 
                content, 
                "Интеграционный сбой: случайное значение метрики не найдено в результирующем файле."
            )

    def test_default_dispatch_integration(self):
        default_report_path = os.path.join(self.repo_path, "report.json")
        result = self.dispatcher.dispatch()
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(default_report_path),
            "Интеграционный сбой: метод по умолчанию не создал report.json в целевом репозитории."
        )


if __name__ == "__main__":
    unittest.main()