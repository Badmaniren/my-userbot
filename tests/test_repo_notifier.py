import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.repo_notifier import RepoNotifier


class TestRepoNotifier(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex[:8]}"

    def test_init_sets_repo_path_and_collaborators(self):
        with patch('skills.repo_notifier.RepoReporter') as mock_reporter_cls, \
             patch('skills.repo_notifier.RepoAutoCommitter') as mock_committer_cls:
            
            notifier = RepoNotifier(self.repo_path)
            
            self.assertEqual(notifier.repo_path, self.repo_path)
            mock_reporter_cls.assert_called_once_with(self.repo_path)
            mock_committer_cls.assert_called_once_with(self.repo_path)

    def test_notify_generates_saves_and_commits(self):
        report_file_path = f"/{uuid.uuid4().hex[:8]}/reports/{uuid.uuid4().hex}.txt"
        expected_content = f"audit_report_{uuid.uuid4().hex}"
        commit_outcome = random.choice([True, False])

        with patch('skills.repo_notifier.RepoReporter') as mock_reporter_cls, \
             patch('skills.repo_notifier.RepoAutoCommitter') as mock_committer_cls:
            
            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.generate_final_report.return_value = expected_content
            
            mock_committer_instance = mock_committer_cls.return_value
            mock_committer_instance.process_and_commit.return_value = commit_outcome

            notifier = RepoNotifier(self.repo_path)
            result = notifier.notify(report_file_path)

            mock_reporter_instance.generate_final_report.assert_called_once()
            mock_reporter_instance.save_report.assert_called_once_with(report_file_path, expected_content)
            mock_committer_instance.process_and_commit.assert_called_once()
            self.assertEqual(result, commit_outcome)

    def test_notify_and_commit_uses_default_path_and_commits(self):
        expected_content = f"summary_data_{uuid.uuid4().hex}"
        expected_default_path = f"{self.repo_path}/report.txt"
        commit_outcome = random.choice([True, False])

        with patch('skills.repo_notifier.RepoReporter') as mock_reporter_cls, \
             patch('skills.repo_notifier.RepoAutoCommitter') as mock_committer_cls:
            
            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.generate_final_report.return_value = expected_content
            
            mock_committer_instance = mock_committer_cls.return_value
            mock_committer_instance.process_and_commit.return_value = commit_outcome

            notifier = RepoNotifier(self.repo_path)
            result = notifier.notify_and_commit()

            mock_reporter_instance.generate_final_report.assert_called_once()
            mock_reporter_instance.save_report.assert_called_once_with(expected_default_path, expected_content)
            mock_committer_instance.process_and_commit.assert_called_once()
            self.assertEqual(result, commit_outcome)


if __name__ == "__main__":
    unittest.main()