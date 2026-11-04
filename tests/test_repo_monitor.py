import unittest
from unittest.mock import patch, MagicMock
import subprocess
import uuid
import random
import string
from skills.repo_monitor import GitCommitter, RepoMonitor


class TestGitCommitterAndRepoMonitor(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.committer = GitCommitter(self.random_repo_path)
        self.monitor = RepoMonitor(self.random_repo_path)

    def test_git_committer_init(self):
        expected_path = f"/var/repo/{uuid.uuid4().hex}"
        committer = GitCommitter(expected_path)
        self.assertEqual(committer.repo_path, expected_path)

    def test_repo_monitor_init(self):
        expected_path = f"/opt/git/{uuid.uuid4().hex}"
        monitor = RepoMonitor(expected_path)
        self.assertEqual(monitor.repo_path, expected_path)

    def test_commit_success(self):
        random_msg = f"Commit message {uuid.uuid4().hex}"
        
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            result = self.committer.commit(random_msg)

            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["git", "-C", self.random_repo_path, "commit", "-m", random_msg],
                capture_output=True,
                text=True
            )

    def test_commit_failure_returncode(self):
        random_msg = f"Failed commit {uuid.uuid4().hex}"
        
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = random.randint(1, 255)
            mock_run.return_value = mock_result

            result = self.committer.commit(random_msg)

            self.assertFalse(result)

    def test_commit_exception_handling(self):
        random_msg = f"Exception commit {uuid.uuid4().hex}"
        
        with patch("subprocess.run", side_effect=Exception("Git binary missing")):
            result = self.committer.commit(random_msg)
            self.assertFalse(result)

    def test_commit_changes_success(self):
        random_file = f"src/{uuid.uuid4().hex}.py"
        random_msg = f"Adding file {uuid.uuid4().hex}"

        with patch("subprocess.run") as mock_run:
            mock_add_result = MagicMock()
            mock_add_result.returncode = 0
            
            mock_commit_result = MagicMock()
            mock_commit_result.returncode = 0

            mock_run.side_effect = [mock_add_result, mock_commit_result]

            result = self.committer.commit_changes(random_file, random_msg)

            self.assertTrue(result)
            self.assertEqual(mock_run.call_count, 2)
            mock_run.assert_any_call(
                ["git", "-C", self.random_repo_path, "add", random_file],
                capture_output=True,
                text=True
            )
            mock_run.assert_any_call(
                ["git", "-C", self.random_repo_path, "commit", "-m", random_msg],
                capture_output=True,
                text=True
            )

    def test_commit_changes_add_failure(self):
        random_file = f"lib/{uuid.uuid4().hex}.cpp"
        random_msg = f"Should not commit {uuid.uuid4().hex}"

        with patch("subprocess.run") as mock_run:
            mock_add_result = MagicMock()
            mock_add_result.returncode = random.randint(1, 100)
            mock_run.return_value = mock_add_result

            result = self.committer.commit_changes(random_file, random_msg)

            self.assertFalse(result)
            mock_run.assert_called_once()

    def test_commit_changes_exception_handling(self):
        random_file = f"docs/{uuid.uuid4().hex}.md"
        random_msg = f"Exception during changes {uuid.uuid4().hex}"

        with patch("subprocess.run", side_effect=Exception("Disk full")):
            result = self.committer.commit_changes(random_file, random_msg)
            self.assertFalse(result)

    def test_check_status_success(self):
        random_status_output = f" M {uuid.uuid4().hex}.py\n?? {uuid.uuid4().hex}.txt\n"

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = random_status_output
            mock_run.return_value = mock_result

            status = self.monitor.check_status()

            self.assertEqual(status, random_status_output)
            mock_run.assert_called_once_with(
                ["git", "-C", self.random_repo_path, "status", "--porcelain"],
                capture_output=True,
                text=True
            )

    def test_check_status_nonzero_returncode(self):
        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.returncode = random.randint(1, 50)
            mock_result.stdout = f"Corrupted repo {uuid.uuid4().hex}"
            mock_run.return_value = mock_result

            status = self.monitor.check_status()

            self.assertEqual(status, "")

    def test_check_status_exception_handling(self):
        with patch("subprocess.run", side_effect=Exception("Not a git repository")):
            status = self.monitor.check_status()
            self.assertEqual(status, "")


if __name__ == "__main__":
    unittest.main()