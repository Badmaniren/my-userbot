import unittest
import os
import uuid
import tempfile
from skills.repo_notifier import RepoNotifier
from skills.repo_reporter import RepoReporter
from skills.repo_auto_committer import RepoAutoCommitter


class TestRepoNotifierIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        # Инициализация реального репозитория через Git, чтобы RepoAutoCommitter не падал
        os.system(f"git init {self.repo_path}")
        os.system(f"git -C {self.repo_path} config user.name 'Architect Test'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")

        self.notifier = RepoNotifier(self.repo_path)
        
        # Генерация уникальных данных для теста
        self.unique_id = str(uuid.uuid4())
        self.report_filename = f"report_{self.unique_id}.txt"
        self.report_path = os.path.join(self.repo_path, self.report_filename)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_notify_integration(self):
        result = self.notifier.notify(self.report_path)
        
        self.assertTrue(result, "Метод notify должен вернуть True при успешном коммите")
        self.assertTrue(
            os.path.exists(self.report_path), 
            "Файл отчета должен быть реально создан в файловой системе"
        )
        
        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIsInstance(content, str)

    def test_notify_and_commit_integration(self):
        default_report_path = os.path.join(self.repo_path, "report.txt")
        
        result = self.notifier.notify_and_commit()
        
        self.assertTrue(result, "Метод notify_and_commit должен вернуть True")
        self.assertTrue(
            os.path.exists(default_report_path), 
            "Дефолтный файл отчета report.txt должен быть создан"
        )


if __name__ == "__main__":
    unittest.main()