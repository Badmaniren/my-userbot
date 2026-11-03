import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os
from skills.repo_backup import GitCommitter, RepoAutoCommitter, RepoMonitor, RepoSummarizer, RepoNotifier, RepoReporter

class TestRepoBackupArchitectInquisitor(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/repo_{uuid.uuid4().hex[:8]}"
        self.rand_msg = f"commit_{uuid.uuid4().hex}"
        self.rand_file = f"file_{uuid.uuid4().hex[:6]}.py"
        self.rand_content = f"content_{uuid.uuid4().hex}".encode('utf-8')

    def test_git_committer_commit_success(self):
        committer = GitCommitter(self.rand_repo)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            res = committer.commit(self.rand_msg)
            self.assertTrue(res)
            mock_run.assert_called()

    def test_git_committer_commit_failure(self):
        committer = GitCommitter(self.rand_repo)
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception(uuid.uuid4().hex)
            res = committer.commit(self.rand_msg)
            self.assertFalse(res)

    def test_git_committer_commit_changes(self):
        committer = GitCommitter(self.rand_repo)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            res = committer.commit_changes(self.rand_file, self.rand_msg)
            self.assertTrue(res)
            self.assertGreaterEqual(mock_run.call_count, 2)

    def test_repo_auto_committer_run(self):
        auto_committer = RepoAutoCommitter(self.rand_repo)
        with patch.object(auto_committer, 'process_and_commit', return_value=True) as mock_proc:
            res = auto_committer.run()
            self.assertTrue(res)
            mock_proc.assert_called_once()

    def test_repo_auto_committer_process_and_commit(self):
        auto_committer = RepoAutoCommitter(self.rand_repo)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            res = auto_committer.process_and_commit()
            self.assertIsInstance(res, bool)

    def test_repo_monitor_check_status(self):
        monitor = RepoMonitor(self.rand_repo)
        expected_status = f"status_{uuid.uuid4().hex[:6]}"
        with patch('subprocess.run') as mock_run:
            mock_proc_instance = MagicMock()
            mock_proc_instance.returncode = 0
            mock_proc_instance.stdout = expected_status
            mock_run.return_value = mock_proc_instance
            
            status = monitor.check_status()
            self.assertIn(expected_status, status)

    def test_repo_summarizer_generate_summary(self):
        summarizer = RepoSummarizer(self.rand_repo)
        rand_summary = f"summary_{uuid.uuid4().hex}"
        with patch('subprocess.run') as mock_run:
            mock_proc_instance = MagicMock()
            mock_proc_instance.returncode = 0
            mock_proc_instance.stdout = rand_summary
            mock_run.return_value = mock_proc_instance
            
            summary = summarizer.generate_summary()
            self.assertIsInstance(summary, str)

    def test_repo_notifier_notify(self):
        notifier = RepoNotifier(self.rand_repo)
        report_path = f"/tmp/{uuid.uuid4().hex}.txt"
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = self.rand_content
            res = notifier.notify(report_path)
            self.assertIsInstance(res, bool)

    def test_repo_notifier_notify_and_commit(self):
        notifier = RepoNotifier(self.rand_repo)
        with patch.object(notifier, 'notify', return_value=True) as mock_n:
            res = notifier.notify_and_commit()
            self.assertIsInstance(res, bool)
            mock_n.assert_called_once()

    def test_repo_reporter_generate_final_report(self):
        reporter = RepoReporter(self.rand_repo)
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = uuid.uuid4().hex
            res = reporter.generate_final_report()
            self.assertIsInstance(res, str)

    def test_repo_reporter_save_report(self):
        reporter = RepoReporter(self.rand_repo)
        out_path = f"/tmp/{uuid.uuid4().hex}.md"
        content = f"# Report {uuid.uuid4().hex}"
        with patch('builtins.open', create=True) as mock_open:
            res = reporter.save_report(out_path, content)
            self.assertEqual(res, out_path)
            mock_open.assert_called_once_with(out_path, 'w', encoding='utf-8')

    def test_repo_reporter_generate_report(self):
        reporter = RepoReporter(self.rand_repo)
        status = uuid.uuid4().hex
        summary = uuid.uuid4().hex
        out_path = f"/tmp/{uuid.uuid4().hex}.json"
        
        with patch.object(reporter, 'save_report', return_value=out_path) as mock_save:
            res = reporter.generate_report(status, summary, out_path)
            self.assertEqual(res, out_path)
            mock_save.assert_called_once()

if __name__ == '__main__':
    unittest.main()