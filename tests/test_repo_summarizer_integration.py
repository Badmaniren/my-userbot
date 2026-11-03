import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_monitor import RepoMonitor, GitCommitter
from skills.repo_summarizer import RepoSummarizer


class TestRepoSummarizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Инициализация git репозитория через bash или используя GitCommitter
        # Создаем базовый коммит, чтобы репозиторий не был пустым
        os.system(f"git init -b main {self.test_dir}")
        os.system(f"git -C {self.test_dir} config user.name 'Test Bot'")
        os.system(f"git -C {self.test_dir} config user.email 'bot@test.com'")
        
        self.committer = GitCommitter(self.test_dir)
        self.monitor = RepoMonitor(self.test_dir)
        self.summarizer = RepoSummarizer(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_summarize_real_repository_changes(self):
        random_file_name = f"feature_{uuid.uuid4().hex[:8]}.txt"
        file_path = os.path.join(self.test_dir, random_file_name)
        
        random_content = f"Task ID: {random.randint(1000, 9999)}, Data: {uuid.uuid4()}"
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_content)

        commit_message = f"Add feature {uuid.uuid4().hex[:6]}"
        commit_success = self.committer.commit_changes(random_file_name, commit_message)
        self.assertTrue(commit_success, "Коммит изменений должен пройти успешно")

        status_output = self.monitor.check_status()
        self.assertIsInstance(status_output, str)

        summary = self.summarizer.generate_summary()

        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0, "Сводка не должна быть пустой")
        self.assertIn(commit_message, summary, "Сводка должна содержать реальное сообщение коммита")
        self.assertIn(random_file_name, summary, "Сводка должна содержать имя измененного файла")


if __name__ == "__main__":
    unittest.main()