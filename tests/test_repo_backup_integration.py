import unittest
import tempfile
import os
import subprocess
import uuid
from skills.repo_backup import (
    GitCommitter,
    RepoAutoCommitter,
    RepoMonitor,
    RepoSummarizer,
    RepoNotifier,
    RepoReporter,
    RepoBackup
)

class TestRepoBackupIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        
        subprocess.run(["git", "init", self.repo_path], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test Architect"], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "architect@test.com"], capture_output=True, check=True)
        
        self.random_filename = f"file_{uuid.uuid4().hex[:8]}.txt"
        self.file_path = os.path.join(self.repo_path, self.random_filename)
        self.file_content = f"content_{uuid.uuid4().hex}"
        
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.file_content)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_backup_and_reporting_pipeline(self):
        committer = GitCommitter(self.repo_path)
        commit_message = f"Commit message {uuid.uuid4().hex[:6]}"
        commit_success = committer.commit_changes(self.random_filename, commit_message)
        self.assertTrue(commit_success, "GitCommitter should successfully commit changes.")

        auto_committer = RepoAutoCommitter(self.repo_path)
        auto_result = auto_committer.run()
        self.assertTrue(auto_result, "RepoAutoCommitter should run successfully.")

        monitor = RepoMonitor(self.repo_path)
        status_output = monitor.check_status()
        self.assertIsInstance(status_output, str, "RepoMonitor status should be a string.")

        summarizer = RepoSummarizer(self.repo_path)
        summary = summarizer.generate_summary()
        self.assertIn(commit_message, summary, "RepoSummarizer summary should contain the recent commit message.")

        reporter = RepoReporter(self.repo_path)
        final_report = reporter.generate_final_report()
        self.assertNotEqual(final_report, "Error", "RepoReporter should generate a valid final report.")
        self.assertNotEqual(final_report, "No commits", "RepoReporter should find at least one commit.")

        report_filename = f"report_{uuid.uuid4().hex[:8]}.txt"
        report_path = os.path.join(self.repo_path, report_filename)
        saved_path = reporter.generate_report(status=status_output, summary=summary, out_path=report_path)
        self.assertTrue(os.path.exists(saved_path), "Report file must be physically created on disk.")

        notifier = RepoNotifier(self.repo_path)
        notify_result = notifier.notify(saved_path)
        self.assertTrue(notify_result, "RepoNotifier should successfully process the generated report.")

        backup_module = RepoBackup(self.repo_path)
        backup_res = backup_module.backup()
        self.assertTrue(backup_res, "RepoBackup should execute backup successfully.")

if __name__ == "__main__":
    unittest.main()