import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
from skills.repo_summarizer import RepoSummarizer


class TestRepoSummarizer(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.summarizer = RepoSummarizer(self.random_repo_path)

    def test_init_sets_repo_path(self):
        self.assertEqual(self.summarizer.repo_path, self.random_repo_path)

    def test_generate_summary_success(self):
        expected_status = f"Status_{uuid.uuid4().hex[:8]}"
        expected_commit_hash = uuid.uuid4().hex
        random_diff_line = f"file_{uuid.uuid4().hex[:4]}.py changed with {random.randint(1, 100)} insertions"
        
        mock_monitor_instance = MagicMock()
        mock_monitor_instance.check_status.return_value = expected_status

        mock_committer_instance = MagicMock()

        with patch("skills.repo_summarizer.RepoMonitor", return_value=mock_monitor_instance) as mock_monitor_cls, \
             patch("skills.repo_summarizer.GitCommitter", return_value=mock_committer_instance) as mock_committer_cls, \
             patch("subprocess.run") as mock_subprocess_run:
            
            mock_process_result = MagicMock()
            mock_process_result.stdout = f"{expected_commit_hash}\t{random_diff_line}\n".encode('utf-8')
            mock_process_result.returncode = 0
            mock_subprocess_run.return_value = mock_process_result

            summary = self.summarizer.generate_summary()

            mock_monitor_cls.assert_called_once_with(self.random_repo_path)
            mock_monitor_instance.check_status.assert_called_once()
            mock_subprocess_run.assert_called_once()

            self.assertIn(expected_status, summary)
            self.assertIn(expected_commit_hash, summary)
            self.assertIn(random_diff_line, summary)

    def test_generate_summary_handles_monitor_exception(self):
        random_error_message = f"error_{uuid.uuid4().hex}"

        mock_monitor_instance = MagicMock()
        mock_monitor_instance.check_status.side_effect = Exception(random_error_message)

        with patch("skills.repo_summarizer.RepoMonitor", return_value=mock_monitor_instance):
            summary = self.summarizer.generate_summary()

            self.assertIn(random_error_message, summary)

    def test_generate_summary_handles_subprocess_failure(self):
        expected_status = f"Clean_status_{uuid.uuid4().hex[:6]}"

        mock_monitor_instance = MagicMock()
        mock_monitor_instance.check_status.return_value = expected_status

        with patch("skills.repo_summarizer.RepoMonitor", return_value=mock_monitor_instance), \
             patch("subprocess.run", side_effect=Exception("Git command failed")) as mock_subprocess_run:

            summary = self.summarizer.generate_summary()

            mock_subprocess_run.assert_called_once()
            self.assertIn(expected_status, summary)
            self.assertIn("Git command failed", summary)


if __name__ == "__main__":
    unittest.main()