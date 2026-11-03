import unittest
from unittest.mock import patch
import uuid
import random
import string
import io

from skills.repo_auto_committer import RepoAutoCommitter


class TestRepoAutoCommitter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex[:8]}"

    def test_auto_committer_no_changes(self):
        random_status = ""
        random_summary = f"Summary_{uuid.uuid4().hex[:6]}"

        with patch("skills.repo_auto_committer.RepoMonitor") as mock_monitor_cls, \
             patch("skills.repo_auto_committer.RepoSummarizer") as mock_summarizer_cls, \
             patch("skills.repo_auto_committer.GitCommitter") as mock_committer_cls:

            mock_monitor = mock_monitor_cls.return_value
            mock_monitor.check_status.return_value = random_status

            mock_summarizer = mock_summarizer_cls.return_value
            mock_summarizer.generate_summary.return_value = random_summary

            mock_committer = mock_committer_cls.return_value

            committer = RepoAutoCommitter(self.repo_path)
            result = committer.run()

            self.assertFalse(result)
            mock_monitor_cls.assert_called_once_with(self.repo_path)
            mock_summarizer_cls.assert_called_once_with(self.repo_path)
            mock_committer_cls.assert_called_once_with(self.repo_path)
            mock_monitor.check_status.assert_called_once()
            mock_summarizer.generate_summary.assert_not_called()
            mock_committer.commit.assert_not_called()

    def test_auto_committer_with_changes_success(self):
        random_status = f"modified: {uuid.uuid4().hex[:6]}.py"
        random_summary = f"Automated commit: {uuid.uuid4().hex[:10]}"

        with patch("skills.repo_auto_committer.RepoMonitor") as mock_monitor_cls, \
             patch("skills.repo_auto_committer.RepoSummarizer") as mock_summarizer_cls, \
             patch("skills.repo_auto_committer.GitCommitter") as mock_committer_cls:

            mock_monitor = mock_monitor_cls.return_value
            mock_monitor.check_status.return_value = random_status

            mock_summarizer = mock_summarizer_cls.return_value
            mock_summarizer.generate_summary.return_value = random_summary

            mock_committer = mock_committer_cls.return_value
            mock_committer.commit.return_value = True

            committer = RepoAutoCommitter(self.repo_path)
            result = committer.run()

            self.assertTrue(result)
            mock_monitor_cls.assert_called_once_with(self.repo_path)
            mock_summarizer_cls.assert_called_once_with(self.repo_path)
            mock_committer_cls.assert_called_once_with(self.repo_path)
            mock_monitor.check_status.assert_called_once()
            mock_summarizer.generate_summary.assert_called_once()
            mock_committer.commit.assert_called_once_with(random_summary)

    def test_auto_committer_with_changes_commit_fails(self):
        random_status = f"untracked: {uuid.uuid4().hex[:6]}.txt"
        random_summary = f"Summary {uuid.uuid4().hex[:8]}"

        with patch("skills.repo_auto_committer.RepoMonitor") as mock_monitor_cls, \
             patch("skills.repo_auto_committer.RepoSummarizer") as mock_summarizer_cls, \
             patch("skills.repo_auto_committer.GitCommitter") as mock_committer_cls:

            mock_monitor = mock_monitor_cls.return_value
            mock_monitor.check_status.return_value = random_status

            mock_summarizer = mock_summarizer_cls.return_value
            mock_summarizer.generate_summary.return_value = random_summary

            mock_committer = mock_committer_cls.return_value
            mock_committer.commit.return_value = False

            committer = RepoAutoCommitter(self.repo_path)
            result = committer.run()

            self.assertFalse(result)
            mock_monitor.check_status.assert_called_once()
            mock_summarizer.generate_summary.assert_called_once()
            mock_committer.commit.assert_called_once_with(random_summary)


if __name__ == "__main__":
    unittest.main()