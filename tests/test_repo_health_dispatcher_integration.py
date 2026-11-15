import unittest
import os
import uuid
import random
import io
from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.random_suffix = uuid.uuid4().hex[:8]
        self.repo_path = os.path.abspath(f"./test_repo_{self.random_suffix}")
        os.makedirs(self.repo_path, exist_ok=True)
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def tearDown(self):
        if os.path.exists(self.repo_path):
            for root, dirs, files in os.walk(self.repo_path, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                    except OSError:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except OSError:
                        pass
            try:
                os.rmdir(self.repo_path)
            except OSError:
                pass

    def test_dispatch_health_and_notify_integration(self):
        file_name = f"report_{uuid.uuid4().hex[:6]}.json"
        file_path = os.path.join(self.repo_path, file_name)
        
        result = self.dispatcher.dispatch_health_and_notify(file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path), "Интеграционный тест: файл отчета должен быть создан дашбордом.")

    def test_process_stream_and_dispatch_integration(self):
        random_title = f"Metric_{uuid.uuid4().hex[:6]}"
        random_value = random.randint(100, 999)
        stream_content = f'{{"title": "{random_title}", "value": {random_value}}}'
        
        file_name = f"stream_report_{uuid.uuid4().hex[:6]}.json"
        file_path = os.path.join(self.repo_path, file_name)
        
        result = self.dispatcher.process_stream_and_dispatch(stream_content, file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path), "Интеграционный тест: файл из стрима должен быть экспортирован.")

    def test_check_and_notify_critical_integration(self):
        random_title = f"Critical_Alert_{uuid.uuid4().hex[:6]}"
        random_value = random.randint(500, 1000)
        file_name = f"critical_{uuid.uuid4().hex[:6]}.txt"
        file_path = os.path.join(self.repo_path, file_name)
        
        result = self.dispatcher.check_and_notify_critical(random_title, random_value, file_path)
        
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(file_path), "Интеграционный тест: критический виджет должен записать файл на диск.")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(random_title, content, "Интеграционный тест: содержимое файла должно отражать переданный заголовок.")

    def test_dispatch_default_path_integration(self):
        result = self.dispatcher.dispatch()
        expected_report_path = os.path.join(self.repo_path, "report.json")
        
        self.assertIsInstance(result, bool)
        self.assertTrue(os.path.exists(expected_report_path), "Интеграционный тест: стандартный метод dispatch должен создавать report.json.")


if __name__ == "__main__":
    unittest.main()