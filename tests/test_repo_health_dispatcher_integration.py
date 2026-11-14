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
        self.random_title = f"Incident_{self.random_id[:8]}"
        self.random_value = random.randint(100, 999)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_dispatch_health_and_notify_integration(self):
        file_name = f"report_{self.random_id}.json"
        file_path = os.path.join(self.repo_path, file_name)

        result = self.dispatcher.dispatch_health_and_notify(file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(file_path),
            f"Интеграционный сбой: файл отчета {file_path} не был создан связанными навыками."
        )
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertGreater(len(content), 0, "Экспортированный дашборд оказался пустым.")

    def test_process_stream_and_dispatch_integration(self):
        stream_data = f'{{"incident_id": "{self.random_id}", "metric": {self.random_value}}}'
        file_name = f"stream_report_{self.random_id}.json"
        file_path = os.path.join(self.repo_path, file_name)

        result = self.dispatcher.process_stream_and_dispatch(stream_data, file_path)

        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(file_path),
            f"Интеграционный сбой: потоковая обработка не сформировала файл по пути {file_path}."
        )

    def test_check_and_notify_critical_integration(self):
        file_name = f"critical_{self.random_id}.log"
        file_path = os.path.join(self.repo_path, file_name)

        result = self.dispatcher.check_and_notify_critical(
            title=self.random_title,
            value=self.random_value,
            file_path=file_path
        )

        self.assertIsInstance(result, bool)
        self.assertTrue(
            os.path.exists(file_path),
            f"Интеграционный сбой: критический виджет не записал данные в {file_path}."