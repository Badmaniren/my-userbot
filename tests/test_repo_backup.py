import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import io
import tempfile

from skills.repo_backup import (
    GitCommitter,
    RepoAutoCommitter,
    RepoMonitor,
    RepoSummarizer,
    RepoNotifier,
    RepoReporter,
    RepoBackup
)

class TestRepoBackupModule(unittest.TestCase):

    def setUp(self):
        self.repo_path = os.path.join(tempfile.gettempdir(), uuid.uuid4().hex)

    def test_git_committer_commit_success(self):
        committer = GitCommitter(self.repo_path)
        random_msg = uuid.uuid4().hex
        
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            result = committer.commit(random_msg)
            self.assertTrue(result)
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertIn("commit", args)
            self.assertIn(random_msg, args)

    def test_git_committer_commit_failure(self):
        committer = GitCommitter(self.repo_path)
        random_msg = uuid.uuid4().hex
        
        mock_result = MagicMock()
        mock_result.returncode = 128

        with patch("subprocess.run", return_value=mock_result):
            result = committer.commit(random_msg)
            self.assertFalse(result)

    def test_git_committer_commit_changes_success(self):
        committer = GitCommitter(self.repo_path)
        random_file = f"{uuid.uuid4().hex}.txt"
        random_msg = uuid.uuid4().hex

        mock_add_fail = MagicMock()
        mock_add_fail.returncode = 1

        mock_add_success = MagicMock()
        mock_add_success.returncode = 0

        mock_commit_success = MagicMock()
        mock_commit_success.returncode = 0

        with patch("subprocess.run", side_effect=[mock_add_fail, mock_add_success, mock_commit_success]) as mock_run:
            result = committer.commit_changes(random_file, random_msg)
            self.assertTrue(result)
            self.assertEqual(mock_run.call_count, 3)

    def test_repo_auto_committer_run(self):
        auto_committer = RepoAutoCommitter(self.repo_path)
        
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            res_process = auto_committer.process_and_commit()
            res_run = auto_committer.run()
            self.assertTrue(res_process)
            self.assertTrue(res_run)
            self.assertEqual(mock_run.call_count, 2)

    def test_repo_monitor_check_status(self):
        monitor = RepoMonitor(self.repo_path)
        random_output = uuid.uuid4().hex

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = random_output

        with patch("subprocess.run", return_value=mock_result):
            status = monitor.check_status()
            self.assertEqual(status, random_output)

    def test_repo_monitor_check_status_exception(self):
        monitor = RepoMonitor(self.repo_path)

        with patch("subprocess.run", side_effect=Exception("Git error")):
            status = monitor.check_status()
            self.assertEqual(status, "")

    def test_repo_summarizer_generate_summary(self):
        summarizer = RepoSummarizer(self.repo_path)
        random_log = f"{uuid.uuid4().hex} fix bug\n{uuid.uuid4().hex} init commit"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = random_log

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            summary = summarizer.generate_summary()
            self.assertEqual(summary, random_log)
            args = mock_run.call_args[0][0]
            self.assertIn("log", args)

    def test_repo_notifier_notify_success(self):
        notifier = RepoNotifier(self.repo_path)
        random_content = uuid.uuid4().hex
        temp_file = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.txt")
        
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(random_content)

            result = notifier.notify(temp_file)
            self.assertTrue(result)
            
            notif_commit = notifier.notify_and_commit()
            self.assertTrue(notif_commit)
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_repo_notifier_notify_failure(self):
        notifier = RepoNotifier(self.repo_path)
        non_existent = os.path.join(tempfile.gettempdir(), uuid.uuid4().hex)
        
        result = notifier.notify(non_existent)
        self.assertFalse(result)

    def test_repo_reporter_generate_final_report(self):
        reporter = RepoReporter(self.repo_path)
        random_hash = uuid.uuid4().hex

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = f"{random_hash}\n"

        with patch("subprocess.run", return_value=mock_result):
            final_report = reporter.generate_final_report()
            self.assertEqual(final_report, random_hash)

    def test_repo_reporter_save_and_generate_report(self):
        reporter = RepoReporter(self.repo_path)
        out_path = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.txt")
        random_status = uuid.uuid4().hex
        random_summary = uuid.uuid4().hex

        try:
            saved_path = reporter.generate_report(random_status, random_summary, out_path)
            self.assertEqual(saved_path, out_path)

            with open(out_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn(random_status, content)
            self.assertIn(random_summary, content)
        finally:
            if os.path.exists(out_path):
                os.remove(out_path)

    def test_repo_backup_create_and_backup(self):
        backup_manager = RepoBackup(self.repo_path)
        self.assertTrue(backup_manager.create_backup())
        self.assertTrue(backup_manager.backup())