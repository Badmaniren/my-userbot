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
        self.assertTrue(
            os.path.exists(self.file_path),
            "Интеграционный сбой: дашборд не создал файл отчета по реальному пути."
        )
        
        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0, "Файл отчета пустой.")

    def test_process_stream_and_dispatch_integration(self):
        stream_data = f'{{"metric_id": "{self.random_tag}", "value": {random.randint(1, 100)}}}'
        
        result = self.dispatcher.process_stream_and_dispatch(stream_data, self.file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            "Интеграционный сбой: потоковая обработка не сформировала файл отчета."
        )

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.random_tag, content, "Случайный ID потока не найден в экспортированном дашборде.")

    def test_check_and_notify_critical_integration(self):
        title = f"Critical_Incident_{self.random_tag}"
        value = random.randint(500, 1000)
        
        result = self.dispatcher.check_and_notify_critical(title, value, self.file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(self.file_path),
            "Интеграционный сбой: критический виджет не записал данные в целевой файл."
        )

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(title, content, "Заголовок критического инцидента отсутствует в отчете.")
            self.assertIn(str(value), content, "Значение критического инцидента отсутствует в отчете.")

    def test_dispatch_default_integration(self):
        result = self.dispatcher.dispatch()
        
        default_report_path = os.path.join(self.test_dir, "report.json")
        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(default_report_path),
            "Интеграционный сбой: дефолтный метод dispatch() не сгенерировал report.json."
        )


if __name__ == "__main__":
    unittest.main()