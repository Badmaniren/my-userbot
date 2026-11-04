import unittest
import tempfile
import os
import subprocess
import uuid
import random

from skills.repo_analytics import RepoAutoCommitter, RepoMonitor, RepoSummarizer, GitCommitter

class TestRepoAnalyticsIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        subprocess.run(["git", "-C", self.repo_path, "init"], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Architect Bot"], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@example.com"], capture_output=True, check=True)
        
        self.random_file_name = f"file_{uuid.uuid4().hex[:8]}.txt"
        self.file_path = os.path.join(self.repo_path, self.random_file_name)
        
        self.random_content = f"Random metric value: {random.randint(1000, 9999)}"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.random_content)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_analytics_pipeline_integration(self):
        committer = GitCommitter(self.repo_path)
        unique_commit_msg = f"Commit message {uuid.uuid4().hex}"
        
        commit_success = committer.commit_changes(self.file_path, unique_commit_msg)
        self.assertTrue(commit_success, "GitCommitter должен успешно зафиксировать изменения файла.")

        auto_committer = RepoAutoCommitter(self.repo_path)
        
        extra_file_name = f"extra_{uuid.uuid4().hex[:8]}.txt"
        extra_file_path = os.path.join(self.repo_path, extra_file_name)
        with open(extra_file_path, "w", encoding="utf-8") as f:
            f.write(str(uuid.uuid4()))

        auto_commit_run = auto_committer.run()
        self.assertTrue(auto_commit_run, "RepoAutoCommitter должен успешно отработать через run().")

        monitor = RepoMonitor(self.repo_path)
        status_output = monitor.check_status()
        self.assertIsInstance(status_output, str, "RepoMonitor должен возвращать статус в виде строки.")

        summarizer = RepoSummarizer(self.repo_path)
        summary_output = summarizer.generate_summary()
        
        self.assertIsInstance(summary_output, str, "RepoSummarizer должен генерировать сводку в виде строки.")
        self.assertIn(unique_commit_msg, summary_output, "Сводка репозитория должна содержать уникальное сообщение коммита.")

if __name__ == "__main__":
    unittest.main()