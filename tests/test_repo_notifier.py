import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.repo_notifier import RepoNotifier


class TestRepoNotifier(unittest.TestCase):

    def _generate_random_string(self, length: int = 16) -> str:
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_random_path(self) -> str:
        segment_1 = uuid.uuid4().hex
        segment_2 = uuid.uuid4().hex
        return f"/var/repo/{segment_1}/{segment_2}"

    def test_init_sets_attributes_and_instantiates_collaborators(self):
        repo_path = self._generate_random_path()

        with patch("skills.repo_notifier.RepoReporter") as mock_reporter_cls, patch(
            "skills.repo_notifier.RepoAutoCommitter"
        ) as mock_committer_cls:
            mock_reporter_instance = MagicMock()
            mock_committer_instance = MagicMock()
            mock_reporter_cls.return_value = mock_reporter_instance
            mock_committer_cls.return_value = mock_committer_instance

            notifier = RepoNotifier(repo_path)

            mock_reporter_cls.assert_called_once_with(repo_path)
            mock_committer_cls.assert_called_once_with(repo_path)

            self.assertEqual(notifier.repo_path, repo_path)
            self.assertIs(notifier.reporter, mock_reporter_instance)
            self.assertIs(notifier.committer, mock_committer_instance)

    def test_notify_success_coordinates_reporting_and_committing(self):
        repo_path = self._generate_random_path()
        custom_report_path = f"{self._generate_random_path()}/{uuid.uuid4().hex}.log"
        generated_content = (
            f"REPORT_HEADER_{uuid.uuid4().hex}\nINCIDENT_DETAILS_{self._generate_random_string(32)}"
        )
        expected_commit_result = random.choice([True, False])

        with patch("skills.repo_notifier.RepoReporter") as mock_reporter_cls, patch(
            "skills.repo_notifier.RepoAutoCommitter"
        ) as mock_committer_cls:
            mock_reporter = MagicMock()
            mock_committer = MagicMock()
            mock_reporter_cls.return_value = mock_reporter
            mock_committer_cls.return_value = mock_committer

            mock_reporter.generate_final_report.return_value = generated_content
            mock_committer.process_and_commit.return_value = expected_commit_result

            notifier = RepoNotifier(repo_path)
            result = notifier.notify(custom_report_path)

            mock_reporter.generate_final_report.assert_called_once()
            mock_reporter.save_report.assert_called_once_with(custom_report_path, generated_content)
            mock_committer.process_and_commit.assert_called_once()
            self.assertEqual(result, expected_commit_result)

    def test_notify_and_commit_uses_default_report_path(self):
        repo_path = self._generate_random_path()
        expected_default_path = f"{repo_path}/report.txt"
        generated_content = (
            f"CRITICAL_HEALTH_DATA_{uuid.uuid4().hex}_{self._generate_random_string(20)}"
        )
        expected_commit_result = random.choice([True, False])

        with patch("skills.repo_notifier.RepoReporter") as mock_reporter_cls, patch(
            "skills.repo_notifier.RepoAutoCommitter"
        ) as mock_committer_cls:
            mock_reporter = MagicMock()
            mock_committer = MagicMock()
            mock_reporter_cls.return_value = mock_reporter
            mock_committer_cls.return_value = mock_committer

            mock_reporter.generate_final_report.return_value = generated_content
            mock_committer.process_and_commit.return_value = expected_commit_result

            notifier = RepoNotifier(repo_path)
            result = notifier.notify_and_commit()

            mock_reporter.generate_final_report.assert_called_once()
            mock_reporter.save_report.assert_called_once_with(expected_default_path, generated_content)
            mock_committer.process_and_commit.assert_called_once()
            self.assertEqual(result, expected_commit_result)

    def test_notify_aborts_and_propagates_if_generate_report_fails(self):
        repo_path = self._generate_random_path()
        target_file = f"{self._generate_random_path()}/output_{uuid.uuid4().hex}.txt"
        err_msg = f"ReportGenException_{uuid.uuid4().hex}"

        with patch("skills.repo_notifier.RepoReporter") as mock_reporter_cls, patch(
            "skills.repo_notifier.RepoAutoCommitter"
        ) as mock_committer_cls:
            mock_reporter = MagicMock()
            mock_committer = MagicMock()
            mock_reporter_cls.return_value = mock_reporter
            mock_committer_cls.return_value = mock_committer

            mock_reporter.generate_final_report.side_effect = RuntimeError(err_msg)

            notifier = RepoNotifier(repo_path)

            with self.assertRaises(RuntimeError) as ctx:
                notifier.notify(target_file)

            self.assertIn(err_msg, str(ctx.exception))
            mock_reporter.save_report.assert_not_called()
            mock_committer.process_and_commit.assert_not_called()

    def test_notify_aborts_and_propagates_if_save_report_fails(self):
        repo_path = self._generate_random_path()
        target_file = f"{self._generate_random_path()}/output_{uuid.uuid4().hex}.txt"
        err_msg = f"SaveReportError_{uuid.uuid4().hex}"
        report_payload = f"Payload_{uuid.uuid4().hex}"

        with patch("skills.repo_notifier.RepoReporter") as mock_reporter_cls, patch(
            "skills.repo_notifier.RepoAutoCommitter"
        ) as mock_committer_cls:
            mock_reporter = MagicMock()
            mock_committer = MagicMock()
            mock_reporter_cls.return_value = mock_reporter
            mock_committer_cls.return_value = mock_committer

            mock_reporter.generate_final_report.return_value = report_payload
            mock_reporter.save_report.side_effect = IOError(err_msg)

            notifier = RepoNotifier(repo_path)

            with self.assertRaises(IOError) as ctx:
                notifier.notify(target_file)

            self.assertIn(err_msg, str(ctx.exception))
            mock_reporter.save_report.assert_called_once_with(target_file, report_payload)
            mock_committer.process_and_commit.assert_not_called()

    def test_notify_and_commit_propagates_commit_failure(self):
        repo_path = self._generate_random_path()
        err_msg = f"GitCommitError_{uuid.uuid4().hex}"
        report_payload = f"Payload_{uuid.uuid4().hex}"
        expected_default_path = f"{repo_path}/report.txt"

        with patch("skills.repo_notifier.RepoReporter") as mock_reporter_cls, patch(
            "skills.repo_notifier.RepoAutoCommitter"
        ) as mock_committer_cls:
            mock_reporter = MagicMock()
            mock_committer = MagicMock()
            mock_reporter_cls.return_value = mock_reporter
            mock_committer_cls.return_value = mock_committer

            mock_reporter.generate_final_report.return_value = report_payload
            mock_committer.process_and_commit.side_effect = RuntimeError(err_msg)

            notifier = RepoNotifier(repo_path)

            with self.assertRaises(RuntimeError) as ctx:
                notifier.notify_and_commit()

            self.assertIn(err_msg, str(ctx.exception))
            mock_reporter.save_report.assert_called_once_with(expected_default_path, report_payload)
            mock_committer.process_and_commit.assert_called_once()

    def test_execution_order_in_notify(self):
        repo_path = self._generate_random_path()
        file_path = f"{self._generate_random_path()}/{uuid.uuid4().hex}.log"
        execution_trace = []

        with patch("skills.repo_notifier.RepoReporter") as mock_reporter_cls, patch(
            "skills.repo_notifier.RepoAutoCommitter"
        ) as mock_committer_cls:
            mock_reporter = MagicMock()
            mock_committer = MagicMock()
            mock_reporter_cls.return_value = mock_reporter
            mock_committer_cls.return_value = mock_committer

            def track_generate():
                execution_trace.append("generate")
                return "trace_content"

            def track_save(path, content):
                execution_trace.append(f"save:{path}")

            def track_commit():
                execution_trace.append("commit")
                return True

            mock_reporter.generate_final_report.side_effect = track_generate
            mock_reporter.save_report.side_effect = track_save
            mock_committer.process_and_commit.side_effect = track_commit

            notifier = RepoNotifier(repo_path)
            notifier.notify(file_path)

            expected_trace = ["generate", f"save:{file_path}", "commit"]
            self.assertEqual(execution_trace, expected_trace)


if __name__ == "__main__":
    unittest.main()