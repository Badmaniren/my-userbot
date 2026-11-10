import unittest
import os
import uuid
import random
import tempfile
from skills.repo_health_dispatcher import RepoHealthDispatcher

class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.dispatcher = RepoHealthDispatcher(self.repo_path)
        
        self.random_id = str(uuid.uuid4())
        self.random_metric_value = random.randint(100, 999)
        self.report_filename = f"report_{self.random_id}.json"
        self.file_path = os.path.join(self.repo_path, self.report_filename)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dispatch_health_and_notify_integration(self):
        result = self.dispatcher.dispatch_health_and_notify(self.file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            f"Интеграционный сбой: файл отчета {self.file_path} не был создан связанными навыками."
        )

    def test_process_stream_and_dispatch_integration(self):
        stream_data = f'{{"metric_id": "{self.random_id}", "value": {self.random_metric_value}}}'
        
        result = self.dispatcher.process_stream_and_dispatch(stream_data, self.file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            f"Интеграционный сбой: потоковые данные не были обработаны и экспортированы в {self.file_path}."
        )
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.random_id, content, "Случайный UUID отсутствует в обработанном потоке данных.")

    def test_check_and_notify_critical_integration(self):
        widget_title = f"Critical_Alert_{self.random_id}"
        
        result = self.dispatcher.check_and_notify_critical(widget_title, self.random_metric_value, self.file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            f"Интеграционный сбой: критический виджет не записан по пути {self.file_path}."
        )
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(widget_title, content, "Заголовок критического виджета не найден в сгенерированном файле.")
            self.assertIn(str(self.random_metric_value), content, "Случайное значение метрики не найдено в сгенерированном файле.")

    def test_default_dispatch_integration(self):
        default_report_path = os.path.join(self.repo_path, "report.json")
        
        result = self.dispatcher.dispatch()
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(default_report_path),
            "Интеграционный сбой: метод dispatch() по умолчанию не создал 'report.json'."
        )

if __name__ == "__main__":
    unittest.main()