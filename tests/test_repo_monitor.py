import unittest
from unittest.mock import patch, MagicMock
import subprocess
import uuid
import random
import string
from skills.repo_monitor import GitCommitter, RepoMonitor


class TestGitCommitterAndRepoMonitor(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.random_file_path = f"{uuid.uuid4().hex}.py"
        self.random_commit_message = ''.join(random.choices(string.ascii_letters + string.whitespace, k=15))
        self.random_status_output = f" M {uuid.uuid4().hex}.txt\n?? {uuid.uuid4().hex}.py\n"

    @patch("subprocess.run")
    def test_git_committer_commit_success(self, mock_subprocess_run):
        mock_completed = MagicMock()
        mock_completed.returncode = 0
        mock_subprocess_run.return_value = mock_completed

        committer = GitCommitter(self.random_repo_path)
        result = committer.commit(self.random_commit_message)

        self.assertTrue(result)
        mock_subprocess_run.assert_called_once_with(
            ["git", "-C", self.random_repo_path, "commit", "-m", self.random_commit_message],
            capture_output=True,
            text=True
        )

    @patch("subprocess.run")
    def test_git_committer_commit_failure(self, mock_subprocess_run):
        mock_completed = MagicMock()
        mock_completed.returncode = random.randint(1, 255)
        mock_subprocess_run.return_value = mock_completed

        committer = GitCommitter(self.random_repo_path)
        result = committer.commit(self.random_commit_message)

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_git_committer_commit_exception(self, mock_subprocess_run):
        mock_subprocess_run.side_effect = Exception(uuid.uuid4().hex)

        committer = GitCommitter(self.random_repo_path)
        result = committer.commit(self.random_commit_message)

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_git_committer_commit_changes_success(self, mock_subprocess_run):
        mock_add = MagicMock()
        mock_add.returncode = 0
        mock_commit = MagicMock()
        mock_commit.returncode = 0

        mock_subprocess_run.side_effect = [mock_add, mock_commit]

        committer = GitCommitter(self.random_repo_path)
        result = committer.commit_changes(self.random_file_path, self.random_commit_message)

        self.assertTrue(result)
        self.assertEqual(mock_subprocess_run.call_count, 2)
        mock_subprocess_run.assert_any_call(
            ["git", "-C", self.random_repo_path, "add", self.random_file_path],
            capture_output=True,
            text=True
        )
        mock_subprocess_run.assert_any_call(
            ["git", "-C", self.random_repo_path, "commit", "-m", self.random_commit_message],
            capture_output=True,
            text=True
        )

    @patch("subprocess.run")
    def test_git_committer_commit_changes_add_failure(self, mock_subprocess_run):
        mock_add = MagicMock()
        mock_add.returncode = random.randint(1, 255)
        mock_subprocess_run.return_value = mock_add

        committer = GitCommitter(self.random_repo_path)
        result = committer.commit_changes(self.random_file_path, self.random_commit_message)

        self.assertFalse(result)
        mock_subprocess_run.assert_called_once_with(
            ["git", "-C", self.random_repo_path, "add", self.random_file_path],
            capture_output=True,
            text=True
        )

    @patch("subprocess.run")
    def test_git_committer_commit_changes_exception(self, mock_subprocess_run):
        mock_subprocess_run.side_effect = Exception(uuid.uuid4().hex)

        committer = GitCommitter(self.random_repo_path)
        result = committer.commit_changes(self.random_file_path, self.random_commit_message)

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_repo_monitor_check_status_success(self, mock_subprocess_run):
        mock_completed = MagicMock()
        mock_completed.returncode = 0
        mock_completed.stdout = self.random_status_output
        mock_subprocess_run.return_value = mock_completed

        monitor = RepoMonitor(self.random_repo_path)
        status = monitor.check_status()

        self.assertEqual(status, self.random_status_output)
        mock_subprocess_run.assert_called_once_with(
            ["git", "-C", self.random_repo_path, "status", "--porcelain"],
            capture_output=True,
            text=True
        )

    @patch("subprocess.run")
    def test_repo_monitor_check_status_nonzero_returncode(self, mock_subprocess_run):
        mock_completed = MagicMock()
        mock_completed.returncode = random.randint(1, 255)
        mock_completed.stdout = self.random_status_output
        mock_subprocess_run.return_value = mock_completed

        monitor = RepoMonitor(self.random_repo_path)
        status = monitor.check_status()

        self.assertEqual(status, "")

    @patch("subprocess.run")
    def test_repo_monitor_check_status_exception(self, mock_subprocess_run):
        mock_subprocess_run.side_effect = Exception(uuid.uuid4().hex)

        monitor = RepoMonitor(self.random_repo_path)
        status = monitor.check_status()

        self.assertEqual(status, "")


if __name__ == "__main__":
    unittest.main()