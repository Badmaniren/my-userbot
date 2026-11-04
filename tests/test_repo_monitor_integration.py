import unittest
import tempfile
import shutil
import os
import subprocess
import uuid
from skills.repo_monitor import RepoMonitor, GitCommitter

class TestRepoMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "init", self.test_dir], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Architect Test"], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "architect@test.com"], capture_output=True, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_monitor_and_committer_integration(self):
        unique_filename = f"file_{uuid.uuid4()}.txt"
        unique_content = str(uuid.uuid4())
        unique_message = f"Commit message {uuid.uuid4()}"

        file_path = os.path.join(self.test_dir, unique_filename)
        with open(file_path, "w") as f:
            f.write(unique_content)

        monitor = RepoMonitor(self.test_dir)
        status_output_before = monitor.check_status()
        self.assertIn(unique_filename, status_output_before)

        committer = GitCommitter(self.test_dir)
        commit_success = committer.commit_changes(unique_filename, unique_message)
        self.assertTrue(commit_success)

        status_output_after = monitor.check_status()
        self.assertEqual(status_output_after.strip(), "")

        log_cmd = ["git", "-C", self.test_dir, "log", "-1", "--pretty=format:%s"]
        log_result = subprocess.run(log_cmd, capture_output=True, text=True, check=True)
        self.assertEqual(log_result.stdout, unique_message)

if __name__ == "__main__":
    unittest.main()