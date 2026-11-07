import unittest
import tempfile
import os
import shutil
import uuid
import random
from skills.repo_monitor import RepoMonitor, GitCommitter


class TestRepoMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        init_cmd = ["git", "init", self.test_dir]
        import subprocess
        subprocess.run(init_cmd, capture_output=True, check=True)
        
        config_name = ["git", "-C", self.test_dir, "config", "user.name", "Architect Test"]
        config_email = ["git", "-C", self.test_dir, "config", "user.email", "architect@test.com"]
        subprocess.run(config_name, capture_output=True, check=True)
        subprocess.run(config_email, capture_output=True, check=True)

        self.monitor = RepoMonitor(self.test_dir)
        self.committer = GitCommitter(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_monitor_and_committer_integration(self):
        random_suffix = uuid.uuid4().hex[:8]
        file_name = f"metric_report_{random_suffix}.txt"
        file_path = os.path.join(self.test_dir, file_name)
        
        random_metric_value = random.randint(1000, 99999)
        file_content = f"resource_optimization_metric: {random_metric_value}"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        status_output_before = self.monitor.check_status()
        self.assertIn(file_name, status_output_before, "Новый файл должен отображаться в статусе репозитория до коммита")
        self.assertIn("??", status_output_before, "Файл должен быть в untracked статусе")

        commit_message = f"Add optimization metrics baseline {random_suffix}"
        commit_success = self.committer.commit_changes(file_name, commit_message)
        self.assertTrue(commit_success, "Коммит изменений должен завершиться успешно")

        status_output_after = self.monitor.check_status()
        self.assertEqual(status_output_after.strip(), "", "После успешного коммита репозиторий должен быть чистым")


if __name__ == "__main__":
    unittest.main()