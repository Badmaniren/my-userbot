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

    def test_auto_commit_success_pipeline(self):
        random_status = ''.join(random.choices(string.ascii_letters + string.digits, k=25))
        random_summary = f"Summary: {''.join(random.choices(string.ascii_letters, k=15))}"

        with patch('skills.repo_auto_committer.RepoMonitor') as MockMonitor, \
             patch('skills.repo_auto_committer.RepoSummarizer') as MockSummarizer, \
             patch('skills.repo_auto_committer.GitCommitter') as MockCommitter:

            instance_monitor = MockMonitor.return_value
            instance_monitor.check_status.return_value = random_status

            instance_summarizer = MockSummarizer.return_value
            instance_summarizer.generate_summary.return_value = random_summary

            instance_committer = MockCommitter.return_value
            instance_committer.commit.return_value = True

            auto_committer = RepoAutoCommitter(self.repo_path)
            result = auto_committer.run()

            MockMonitor.assert_called_once_with(self.repo_path)
            instance_monitor.check_status.assert_called_once()

            MockSummarizer.assert_called_once_with(self.repo_path)
            instance_summarizer.generate_summary.assert_called_once()

            MockCommitter.assert_called_once_with(self.repo_path)
            instance_committer.commit.assert_called_once_with(random_summary)

            self.assertTrue(result)

    def test_auto_commit_no_changes_detected(self):
        with patch('skills.repo_auto_committer.RepoMonitor') as MockMonitor, \
             patch('skills.repo_auto_committer.RepoSummarizer') as MockSummarizer, \
             patch('skills.repo_auto_committer.GitCommitter') as MockCommitter:

            instance_monitor = MockMonitor.return_value
            instance_monitor.check_status.return_value = ""

            auto_committer = RepoAutoCommitter(self.repo_path)
            result = auto_committer.run()

            instance_monitor.check_status.assert_called_once()
            MockSummarizer.assert_not_called()
            MockCommitter.assert_not_called()
            self.assertFalse(result)

    def test_auto_commit_commit_failure(self):
        random_status = uuid.uuid4().hex
        random_summary = uuid.uuid4().hex

        with patch('skills.repo_auto_committer.RepoMonitor') as MockMonitor, \
             patch('skills.repo_auto_committer.RepoSummarizer') as MockSummarizer, \
             patch('skills.repo_auto_committer.GitCommitter') as MockCommitter:

            MockMonitor.return_value.check_status.return_value = random_status
            MockSummarizer.return_value.generate_summary.return_value = random_summary

            instance_committer = MockCommitter.return_value
            instance_committer.commit.return_value = False

            auto_committer = RepoAutoCommitter(self.repo_path)
            result = auto_committer.run()

            instance_committer.commit.assert_called_once_with(random_summary)
            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()