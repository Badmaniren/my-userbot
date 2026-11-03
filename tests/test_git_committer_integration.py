import unittest
import subprocess
import uuid
import random
import os
import tempfile
from skills.git_committer import GitCommitter

class TestGitCommitterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        subprocess.run(["git", "init", self.repo_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Architect Bot"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@test.com"], check=True)
        
        self.committer = GitCommitter(repo_path=self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_commit_real_file_integration(self):
        random_filename = f"file_{uuid.uuid4().hex}.txt"
        random_content = f"content_{uuid.uuid4().hex}_{random.randint(1000, 9999)}"
        file_path = os.path.join(self.repo_path, random_filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_content)

        commit_message = f"Add {random_filename} with {uuid.uuid4().hex}"
        
        result = self.committer.commit_changes(file_path=random_filename, message=commit_message)
        
        self.assertTrue(result, "Integration commit failed to return True.")

        log_result = subprocess.run(
            ["git", "-C", self.repo_path, "log", "-1", "--pretty=format:%s"],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(log_result.stdout, commit_message, "Git log does not match the expected commit message.")

        status_result = subprocess.run(
            ["git", "-C", self.repo_path, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(status_result.stdout.strip(), "", "Working tree is not clean after commit.")

    def test_subprocess_exception_handling_integration(self):
        non_existent_file = f"ghost_{uuid.uuid4().hex}.txt"
        random_message = f"Fail commit {uuid.uuid4().hex}"

        result = self.committer.commit_changes(file_path=non_existent_file, message=random_message)
        
        self.assertFalse(result, "Commit should fail gracefully on non-existent files and return False.")

if __name__ == "__main__":
    unittest.main()