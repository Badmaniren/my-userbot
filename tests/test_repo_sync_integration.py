import unittest
import tempfile
import shutil
import os
import uuid
import random
from pathlib import Path
from skills.repo_sync import (
    GitCommitter,
    RepoAutoCommitter,
    RepoMonitor,
    RepoSummarizer,
    RepoNotifier,
    RepoReporter,
    RepoBackup,
    RepoLogger,
    RepoRecovery
)

class TestRepoSyncIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Architect Test'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")

        self.unique_id = str(uuid.uuid4())
        self.test_file_name = f"file_{self.unique_id}.txt"
        self.test_file_path = os.path.join(self.repo_path, self.test_file_name)

        self.random_content = f"Random content payload: {random.randint(1000, 9999)}-{self.unique_id}"
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(self.random_content)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_distributed_pipeline_integration(self):
        logger = RepoLogger(self.repo_path)
        log_event_res = logger.log_event("PIPELINE_START", f"Starting pipeline for {self.unique_id}")
        self.assertTrue(log_event_res)

        monitor = RepoMonitor(self.repo_path)
        status = monitor.check_status()
        self.assertIsInstance(status, str)

        committer = GitCommitter(self.repo_path)
        commit_msg = f"Add test file {self.unique_id}"
        commit_res = committer.commit_changes(self.test_file_name, commit_msg)
        self.assertTrue(commit_res)

        logger.log_git_operation("commit", "SUCCESS")

        summarizer = RepoSummarizer(self.repo_path)
        summary = summarizer.generate_summary()
        self.assertIsInstance(summary, str)

        reporter = RepoReporter(self.repo_path)
        report_filename = f"report_{self.unique_id}.md"
        report_path = os.path.join(self.repo_path, report_filename)

        generated_report = reporter.generate_report(status, summary, report_path)
        self.assertIsInstance(generated_report, str)

        saved_path = reporter.save_report(report_path, f"Finalized report content UUID: {self.unique_id}")
        self.assertTrue(os.path.exists(saved_path))

        notifier = RepoNotifier(self.repo_path)
        notify_res = notifier.notify(report_path)
        self.assertTrue(notify_res)

        backup = RepoBackup(self.repo_path)
        backup_res = backup.create_backup()
        self.assertTrue(backup_res)

        auto_committer = RepoAutoCommitter(self.repo_path)
        auto_res = auto_committer.process_and_commit()
        self.assertTrue(auto_res)

        recovery = RepoRecovery(self.repo_path)
        recovery_res = recovery.recover_repository()
        self.assertTrue(recovery_res)

        logger.log_metric("pipeline_uuid_check", float(random.randint(1, 100)))

        self.assertTrue(os.path.exists(self.test_file_path), "Core test file must remain intact across pipeline operations")
        with open(self.test_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, self.random_content, "File content must not be corrupted")

if __name__ == "__main__":
    unittest.main()