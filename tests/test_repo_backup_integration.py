import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_backup import RepoBackup
from skills.repo_analytics import RepoMonitor, RepoSummarizer
from skills.repo_reporter import RepoReporter
from skills.git_committer import GitCommitter

class TestRepoBackupIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Initialize git repo for testing real interactions
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Arch Test'")
        os.system(f"git -C {self.test_dir} config user.email 'arch@test.com'")
        
        # Generate random initial content
        self.unique_id = str(uuid.uuid4())
        self.file_name = f"file_{uuid.uuid4().hex[:6]}.txt"
        self.file_path = os.path.join(self.test_dir, self.file_name)
        
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(f"Initial content: {self.unique_id}\nRandom value: {random.randint(1, 100000)}")
            
        committer = GitCommitter(self.test_dir)
        committer.commit_changes(self.file_path, f"Initial commit {self.unique_id}")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_repo_backup_full_lifecycle(self):
        # Modify file with new random data
        new_random_data = f"Updated content: {uuid.uuid4()}"
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(new_random_data + "\n")

        # Instantiate real related modules to ensure integration without mocks
        monitor = RepoMonitor(self.test_dir)
        status = monitor.check_status()
        self.assertIsInstance(status, str)

        summarizer = RepoSummarizer(self.test_dir)
        summary = summarizer.generate_summary()
        self.assertIsInstance(summary, str)

        reporter = RepoReporter(self.test_dir)
        report_filename = f"report_{uuid.uuid4().hex[:8]}.txt"
        report_path = os.path.join(self.test_dir, report_filename)
        saved_report = reporter.save_report(report_path, f"Status: {status}\nSummary: {summary}")
        self.assertTrue(os.path.exists(saved_report))

        # Test RepoBackup core functionality
        backup_manager = RepoBackup(self.test_dir)
        
        # Assuming backup creates a snapshot or archive
        backup_result = backup_manager.create_backup() if hasattr(backup_manager, "create_backup") else backup_manager.backup()
        self.assertTrue(backup_result)

if __name__ == "__main__":
    unittest.main()