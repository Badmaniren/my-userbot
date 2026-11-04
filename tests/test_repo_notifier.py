import unittest
from unittest.mock import patch
import uuid
import random
from skills.repo_notifier import RepoNotifier


class TestRepoNotifier(unittest.TestCase):

    def test_notify_success(self):
        repo_path = f"/repo_{uuid.uuid4().hex}"
        report_file_path = f"/path/{uuid.uuid4().hex}.txt"
        random_report_content = f"report_data_{uuid.uuid4().hex}"
        expected_commit_result = random.choice([True, False])

        with patch("skills.repo_notifier.RepoReporter") as MockReporter, \
             patch("skills.repo_notifier.RepoAutoCommitter") as MockCommitter:

            mock_reporter_instance = MockReporter.return_value
            mock_reporter_instance.generate_final_report.return_value = random_report_content

            mock_committer_instance = MockCommitter.return_value
            mock_committer_instance.process_and_commit.return_value = expected_commit_result

            notifier = RepoNotifier(repo_path)
            result = notifier.notify(report_file_path)

            MockReporter.assert_called_once_with(repo_path)
            MockCommitter.assert_called_once_with(repo_path)

            mock_reporter_instance.generate_final_report.assert_called_once()
            mock_reporter_instance.save_report.assert_called_once_with(report_file_path, random_report_content)
            mock_committer_instance.process_and_commit.assert_called_once()

            self.assertEqual(result, expected_commit_result)

    def test_notify_and_commit_success(self):
        repo_path = f"/var/repo_{uuid.uuid4().hex}"
        random_report_content = f"content_{uuid.uuid4().hex}"
        expected_report_path = f"{repo_path}/report.txt"
        expected_commit_result = random.choice([True, False])

        with patch("skills.repo_notifier.RepoReporter") as MockReporter, \
             patch("skills.repo_notifier.RepoAutoCommitter") as MockCommitter:

            mock_reporter_instance = MockReporter.return_value
            mock_reporter_instance.generate_final_report.return_value = random_report_content

            mock_committer_instance = MockCommitter.return_value
            mock_committer_instance.process_and_commit.return_value = expected_commit_result

            notifier = RepoNotifier(repo_path)
            result = notifier.notify_and_commit()

            MockReporter.assert_called_once_with(repo_path)
            MockCommitter.assert_called_once_with(repo_path)

            mock_reporter_instance.generate_final_report.assert_called_once()
            mock_reporter_instance.save_report.assert_called_once_with(expected_report_path, random_report_content)
            mock_committer_instance.process_and_commit.assert_called_once()

            self.assertEqual(result, expected_commit_result)


if __name__ == "__main__":
    unittest.main()