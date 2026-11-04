import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
import uuid
import random
import string
from skills.repo_analytics import GitCommitter, RepoAutoCommitter, RepoMonitor, RepoSummarizer

class TestRepoAnalytics(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.message = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.txt")

    def test_git_committer_commit_success(self):
        committer = GitCommitter(self.repo_path)
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            res = committer.commit(self.message)
            self.assertTrue(res)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "commit", "-am", self.message],
                capture_output=True,
                text=True,
                check=True
            )

    def test_git_committer_commit_failure(self):
        committer = GitCommitter(self.repo_path)
        with patch("subprocess.run", side_effect=subprocess.SubprocessError("git fail")) as mock_run:
            res = committer.commit(self.message)
            self.assertFalse(res)
            mock_run.assert_called_once()

    def test_git_committer_commit_changes_success(self):
        committer = GitCommitter(self.repo_path)
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("os.path.relpath", return_value="relative_dummy.txt") as mock_relpath, \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            res = committer.commit_changes(self.file_path, self.message)
            self.assertTrue(res)
            self.assertEqual(mock_run.call_count, 2)
            mock_relpath.assert_called_once_with(self.file_path, self.repo_path)

    def test_git_committer_commit_changes_failure(self):
        committer = GitCommitter(self.repo_path)
        with patch("os.path.relpath", return_value="relative_dummy.txt"), \
             patch("subprocess.run", side_effect=subprocess.SubprocessError("git add/commit fail")) as mock_run:
            res = committer.commit_changes(self.file_path, self.message)
            self.assertFalse(res)
            mock_run.assert_called_once()

    def test_repo_auto_committer_process_and_commit(self):
        auto_committer = RepoAutoCommitter(self.repo_path)
        with patch.object(GitCommitter, "commit", return_value=True) as mock_commit:
            res = auto_committer.process_and_commit()
            self.assertTrue(res)
            mock_commit.assert_called_once_with("Auto-commit updates")

    def test_repo_auto_committer_process_and_commit_exception(self):
        auto_committer = RepoAutoCommitter(self.repo_path)
        with patch.object(GitCommitter, "commit", side_effect=Exception("Critical error")) as mock_commit:
            res = auto_committer.process_and_commit()
            self.assertFalse(res)
            mock_commit.assert_called_once()

    def test_repo_auto_committer_run(self):
        auto_committer = RepoAutoCommitter(self.repo_path)
        with patch.object(RepoAutoCommitter, "process_and_commit", return_value=True) as mock_proc:
            res = auto_committer.run()
            self.assertTrue(res)
            mock_proc.assert_called_once()

    def test_repo_monitor_check_status_success(self):
        monitor = RepoMonitor(self.repo_path)
        expected_output = f"On branch {uuid.uuid4().hex}\nnothing to commit"
        mock_result = MagicMock()
        mock_result.stdout = expected_output

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            res = monitor.check_status()
            self.assertEqual(res, expected_output)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "status"],
                capture_output=True,
                text=True,
                check=True
            )

    def test_repo_monitor_check_status_exception(self):
        monitor = RepoMonitor(self.repo_path)
        err_msg = f"Err-{uuid.uuid4().hex}"
        with patch("subprocess.run", side_effect=Exception(err_msg)) as mock_run:
            res = monitor.check_status()
            self.assertIn(err_msg, res)
            mock_run.assert_called_once()

    def test_repo_summarizer_generate_summary_success(self):
        summarizer = RepoSummarizer(self.repo_path)
        expected_log = f"{uuid.uuid4().hex[:7]} commit message\n{uuid.uuid4().hex[:7]} another commit"
        mock_result = MagicMock()
        mock_result.stdout = expected_log

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            res = summarizer.generate_summary()
            self.assertEqual(res, expected_log)
            mock_run.assert_called_once_with(
                ["git", "-C", self.repo_path, "log", "-n", "5", "--oneline"],
                capture_output=True,
                text=True,
                check=True
            )

    def test_repo_summarizer_generate_summary_exception(self):
        summarizer = RepoSummarizer(self.repo_path)
        err_msg = f"Fail-{uuid.uuid4().hex}"
        with patch("subprocess.run", side_effect=Exception(err_msg)) as mock_run:
            res = summarizer.generate_summary()
            self.assertIn(err_msg, res)
            mock_run.assert_called_once()

if __name__ == "__main__":
    unittest.main()