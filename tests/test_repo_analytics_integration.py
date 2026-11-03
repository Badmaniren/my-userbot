import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_analytics import (
    GitCommitter,
    RepoAutoCommitter,
    RepoMonitor,
    RepoSummarizer
)

class TestRepoAnalyticsIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Инициализация простого git-репозитория через системные команды для подготовки базы
        os.system(f"git init {self.test_dir}")
        os.system(f"git -C {self.test_dir} config user.name 'Test Bot'")
        os.system(f"git -C {self.test_dir} config user.email 'bot@test.com'")
        
        # Создаем начальный файл и коммит, чтобы HEAD существовал
        self.initial_file = os.path.join(self.test_dir, "README.md")
        with open(self.initial_file, "w", encoding="utf-8") as f:
            f.write(f"Initial content: {uuid.uuid4()}")
        
        os.system(f"git -C {self.test_dir} add README.md")
        os.system(f"git -C {self.test_dir} commit -m 'Initial commit'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_analytics_and_git_workflow(self):
        # Генерируем уникальные данные для теста
        unique_filename = f"file_{uuid.uuid4().hex[:8]}.txt"
        file_path = os.path.join(self.test_dir, unique_filename)
        random_content = f"Random data payload: {uuid.uuid4()} - {random.randint(1000, 9999)}"

        # 1. Создаем файл с рандомными данными
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_content)

        # 2. Проверяем мониторинг репозитория (RepoMonitor) до коммита
        monitor = RepoMonitor(self.test_dir)
        status_before = monitor.check_status()
        self.assertIsInstance(status_before, str)
        self.assertTrue(len(status_before) > 0)

        # 3. Используем GitCommitter для добавления и коммита изменений
        committer = GitCommitter(self.test_dir)
        commit_message = f"Add {unique_filename} with id {uuid.uuid4()}"
        
        commit_result = committer.commit_changes(file_path, commit_message)
        self.assertTrue(commit_result, "GitCommitter должен успешно закомитить изменения файла")

        # 4. Создаем еще один файл через авто-коммитер или проверяем RepoAutoCommitter
        auto_file = os.path.join(self.test_dir, f"auto_{uuid.uuid4().hex[:8]}.py")
        with open(auto_file, "w", encoding="utf-8") as f:
            f.write(f"# Auto generated content {uuid.uuid4()}")

        auto_committer = RepoAutoCommitter(self.test_dir)
        auto_run_result = auto_committer.process_and_commit()
        self.assertIsInstance(auto_run_result, bool)

        # 5. Генерируем общую сводку репозитория (RepoSummarizer)
        summarizer = RepoSummarizer(self.test_dir)
        summary = summarizer.generate_summary()
        
        self.assertIsInstance(summary, str)
        # Проверяем, что в сводке отображаются наши реальные коммиты или файлы
        self.assertTrue(len(summary) > 0)

        # Дополнительная проверка через повторный мониторинг статуса
        status_after = monitor.check_status()
        self.assertIsInstance(status_after, str)

if __name__ == "__main__":
    unittest.main()