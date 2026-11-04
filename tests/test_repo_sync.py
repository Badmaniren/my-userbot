import unittest
from unittest.mock import patch, mock_open
import os
import uuid
import random
import string

from skills.repo_sync import (
    RepoMonitor,
    RepoAutoCommitter,
    RepoReporter,
    RepoLogger,
    RepoSync,
    start_new
)

class TestRepoSyncModule(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.random_report_path = f"/tmp/{uuid.uuid4().hex}.txt"
        self.random_summary_text = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        self.random_event_name = uuid.uuid4().hex
        self.random_details = {uuid.uuid4().hex: uuid.uuid4().hex}

    def test_repo_monitor_check_status(self):
        monitor = RepoMonitor(self.random_repo_path)
        self.assertEqual(monitor.repo_path, self.random_repo_path)
        status = monitor.check_status()
        self.assertIsInstance(status, str)
        self.assertEqual(status, "synced")

    def test_repo_auto_committer_methods(self):
        committer = RepoAutoCommitter(self.random_repo_path)
        self.assertEqual(committer.repo_path, self.random_repo_path)
        self.assertTrue(committer.run())
        self.assertTrue(committer.process_and_commit())

    def test_repo_reporter_generate_and_save(self):
        reporter = RepoReporter(self.random_repo_path)
        self.assertEqual(reporter.repo_path, self.random_repo_path)
        report = reporter.generate_final_report()
        self.assertIsInstance(report, str)
        self.assertIn("Sync completed", report)

        with patch("builtins.open", mock_open()) as mock_file:
            result = reporter.save_report(self.random_report_path, self.random_summary_text)
            self.assertTrue(result)
            mock_file.assert_called_once_with(self.random_report_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(self.random_summary_text)

    def test_repo_reporter_save_report_exception(self):
        reporter = RepoReporter(self.random_repo_path)
        with patch("builtins.open", side_effect=Exception(uuid.uuid4().hex)):
            result = reporter.save_report(self.random_report_path, self.random_summary_text)
            self.assertFalse(result)

    def test_repo_logger_log_event(self):
        logger = RepoLogger(self.random_repo_path)
        self.assertEqual(logger.repo_path, self.random_repo_path)
        success = logger.log_event(self.random_event_name, self.random_details)
        self.assertTrue(success)

    def test_repo_sync_synchronize(self):
        sync = RepoSync(self.random_repo_path)
        self.assertEqual(sync.repo_path, self.random_repo_path)
        self.assertTrue(sync.synchronize())

    def test_start_new_function(self):
        result = start_new(self.random_repo_path)
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("report", result)
        self.assertEqual(result["status"], "synced")
        self.assertIsInstance(result["report"], str)

if __name__ == "__main__":
    unittest.main()