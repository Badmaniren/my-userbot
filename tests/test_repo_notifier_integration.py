import unittest
import os
import uuid
import tempfile
from skills.repo_notifier import RepoNotifier


class TestRepoNotifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        # Инициализируем git репозиторий через системный вызов или полагаемся на поведение навыков, 
        # но так как моки запрещены, создадим минимальную git-среду для корректной работы автокоммитера.
        os.system(f"git init {self.repo_path}")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        
        self.notifier = RepoNotifier(self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_notify_integration_generates_and_commits_random_data(self):
        unique_filename = f"report_{uuid.uuid4().hex}.txt"
        report_path = os.path.join(self.repo_path, unique_filename)

        result = self.notifier.notify(report_path)

        self.assertTrue(result, "Метод notify должен вернуть True при успешном сохранении и коммите")
        self.assertTrue(os.path.exists(report_path), "Файл отчета должен быть реально создан в файловой системе")

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 0, "Сгенерированный отчет не должен быть пустым")

        # Проверяем, что файл действительно попал в git-репозиторий
        git_status_output = os.popen(f"git -C {self.repo_path} status --porcelain").read()
        self.assertEqual(git_status_output.strip(), "", "Все изменения должны быть закоммичены автокоммитером")

    def test_notify_and_commit_integration_default_path(self):
        result = self.notifier.notify_and_commit()

        self.assertTrue(result, "Метод notify_and_commit должен вернуть True")
        default_report_path = os.path.join(self.repo_path, "report.txt")
        self.assertTrue(os.path.exists(default_report_path), "Дефолтный файл отчета report.txt должен быть создан")

        with open(default_report_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertGreater(len(content), 0, "Содержимое дефолтного отчета не должно быть пустым")


if __name__ == "__main__":
    unittest.main()