import unittest
import tempfile
import shutil
import subprocess
import os
import uuid
import random
from skills.git_committer import GitCommitter

class TestGitCommitterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_name = f"repo_{uuid.uuid4().hex[:8]}"
        self.repo_path = os.path.join(self.test_dir, self.repo_name)
        os.makedirs(self.repo_path)

        subprocess.run(["git", "init", self.repo_path], check=True, capture_output=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test Bot"], check=True, capture_output=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "bot@test.local"], check=True, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_commit_and_push_integration(self):
        random_filename = f"file_{uuid.uuid4().hex[:8]}.txt"
        random_content = f"content_{random.randint(1000, 9999)}"
        commit_message = f"feat: auto commit {uuid.uuid4().hex[:6]}"

        file_full_path = os.path.join(self.repo_path, random_filename)
        with open(file_full_path, "w", encoding="utf-8") as f:
            f.write(random_content)

        committer = GitCommitter(repo_path=self.repo_path)

        result_commit_hash = committer.commit_changes(
            file_paths=[random_filename],
            message=commit_message
        )

        self.assertIsNotNone(result_commit_hash)
        self.assertIsInstance(result_commit_hash, str)
        self.assertTrue(len(result_commit_hash) >= 7)

        log_process = subprocess.run(
            ["git", "-C", self.repo_path, "log", "-1", "--pretty=format:%s"],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(log_process.stdout.strip(), commit_message)

        status_process = subprocess.run(
            ["git", "-C", self.repo_path, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(status_process.stdout.strip(), "")

if __name__ == "__main__":
    unittest.main()