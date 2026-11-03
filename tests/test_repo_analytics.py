import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.repo_analytics import (
    GitCommitter,
    RepoAutoCommitter,
    RepoMonitor,
    RepoSummarizer
)


class TestRepoAnalyticsInquisitor(unittest.TestCase):

    def _generate_random_path(self):
        return f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"

    def _generate_random_message(self):
        return ''.join(random.choices(string.ascii_letters + string.whitespace, k=random.randint(10, 50)))

    def test_git_committer_commit(self):
        repo_path = self._generate_random_path()
        msg = self._generate_random_message()

        committer = GitCommitter(repo_path)
        self.assertEqual(committer.repo_path, repo_path)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            result = committer.commit(msg)
            self.assertTrue(result)
            mock_run.assert_called()

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception(uuid.uuid4().hex)
            result = committer.commit(msg)
            self.assertFalse(result)

    def test_git_committer_commit_changes(self):
        repo_path = self._generate_random_path()
        file_path = f"{repo_path}/{uuid.uuid4().hex}.py"
        msg = self._generate_random_message()

        committer = GitCommitter(repo_path)

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            result = committer.commit_changes(file_path, msg)
            self.assertTrue(result)
            self.assertEqual(mock_run.call_count, 2)

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception(uuid.uuid4().hex)
            result = committer.commit_changes(file_path, msg)
            self.assertFalse(result)

    def test_repo_auto_committer_run(self):
        repo_path = self._generate_random_path()
        auto_committer = RepoAutoCommitter(repo_path)

        with patch.object(RepoAutoCommitter, 'process_and_commit') as mock_process:
            mock_process.return_value = True
            result = auto_committer.run()
            self.assertTrue(result)
            mock_process.assert_called_once()

        with patch.object(RepoAutoCommitter, 'process_and_commit') as mock_process:
            mock_process.return_value = False
            result = auto_committer.run()
            self.assertFalse(result)

    def test_repo_auto_committer_process_and_commit(self):
        repo_path = self._generate_random_path()
        auto_committer = RepoAutoCommitter(repo_path)

        with patch('skills.repo_analytics.GitCommitter') as MockGitCommitter:
            instance = MockGitCommitter.return_value
            instance.commit.return_value = True

            result = auto_committer.process_and_commit()
            self.assertTrue(result)
            MockGitCommitter.assert_called_once_with(repo_path)
            instance.commit.assert_called_once()

        with patch('skills.repo_analytics.GitCommitter') as MockGitCommitter:
            instance = MockGitCommitter.return_value
            instance.commit.return_value = False

            result = auto_committer.process_and_commit()
            self.assertFalse(result)

    def test_repo_monitor_check_status(self):
        repo_path = self._generate_random_path()
        expected_output = uuid.uuid4().hex

        monitor = RepoMonitor(repo_path)
        self.assertEqual(monitor.repo_path, repo_path)

        with patch('subprocess.run') as mock_run:
            mock_instance = MagicMock()
            mock_instance.returncode = 0
            mock_instance.stdout = expected_output
            mock_run.return_value = mock_instance

            status = monitor.check_status()
            self.assertEqual(status, expected_output)

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception(uuid.uuid4().hex)
            status = monitor.check_status()
            self.assertIsInstance(status, str)

    def test_repo_summarizer_generate_summary(self):
        repo_path = self._generate_random_path()
        random_summary_fragment = uuid.uuid4().hex

        summarizer = RepoSummarizer(repo_path)
        self.assertEqual(summarizer.repo_path, repo_path)

        with patch('subprocess.run') as mock_run:
            mock_instance = MagicMock()
            mock_instance.returncode = 0
            mock_instance.stdout = random_summary_fragment
            mock_run.return_value = mock_instance

            summary = summarizer.generate_summary()
            self.assertIn(random_summary_fragment, summary)

        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception(uuid.uuid4().hex)
            summary = summarizer.generate_summary()
            self.assertIsInstance(summary, str)


if __name__ == '__main__':
    unittest.main()