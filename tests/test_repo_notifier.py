import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.repo_notifier import RepoNotifier


class TestRepoNotifier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.report_file_path = os.path.join(self.repo_path, f"report_{uuid.uuid4().hex}.txt")

    def test_composition_and_execution_success(self):
        random_status = ''.join(random.choices(string.ascii_letters, k=10))
        random_summary = ''.join(random.choices(string.ascii_letters, k=15))
        random_report_content = ''.join(random.choices(string.ascii_letters, k=25))

        with patch('skills.repo_notifier.RepoReporter') as MockReporter, \
             patch('skills.repo_notifier.RepoAutoCommitter') as MockAutoCommitter:

            reporter_instance = MockReporter.return_value
            reporter_instance.generate_final_report.return_value = random_report_content
            reporter_instance.save_report.return_value = self.report_file_path

            committer_instance = MockAutoCommitter.return_value
            committer_instance.process_and_commit.return_value = True

            notifier = RepoNotifier(self.repo_path)
            result = notifier.notify(self.report_file_path)

            MockReporter.assert_called_once_with(self.repo_path)
            MockAutoCommitter.assert_called_once_with(self.repo_path)
            
            reporter_instance.generate_final_report.assert_called_once()
            reporter_instance.save_report.assert_called_once_with(self.report_file_path, random_report_content)
            committer_instance.process_and_commit.assert_called_once()

            self.assertTrue(result)

    def test_composition_and_execution_committer_failure(self):
        random_report_content = ''.join(random.choices(string.ascii_letters, k=20))

        with patch('skills.repo_notifier.RepoReporter') as MockReporter, \
             patch('skills.repo_notifier.RepoAutoCommitter') as MockAutoCommitter:

            reporter_instance = MockReporter.return_value
            reporter_instance.generate_final_report.return_value = random_report_content
            reporter_instance.save_report.return_value = self.report_file_path

            committer_instance = MockAutoCommitter.return_value
            committer_instance.process_and_commit.return_value = False

            notifier = RepoNotifier(self.repo_path)
            result = notifier.notify(self.report_file_path)

            MockReporter.assert_called_once_with(self.repo_path)
            MockAutoCommitter.assert_called_once_with(self.repo_path)
            
            reporter_instance.generate_final_report.assert_called_once()
            reporter_instance.save_report.assert_called_once_with(self.report_file_path, random_report_content)
            committer_instance.process_and_commit.assert_called_once()

            self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()