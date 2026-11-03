import unittest
import tempfile
import shutil
from pathlib import Path
import uuid
import random

from skills.repo_logger import RepoLogger
from skills.repo_monitor import RepoMonitor
from skills.repo_summarizer import RepoSummarizer
from skills.repo_reporter import RepoReporter
from skills.repo_backup import RepoBackup


class TestRepoLoggerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.test_dir)
        
        import subprocess
        subprocess.run(["git", "init", str(self.repo_path)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo_path), "config", "user.name", "Test User"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.repo_path), "config", "user.email", "test@example.com"], check=True, capture_output=True)

        self.logger = RepoLogger(str(self.repo_path))

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_integration_workflow_without_mocking(self):
        unique_file_name = f"file_{uuid.uuid4()}.txt"
        unique_content = f"content_{uuid.uuid4()}_{random.randint(1000, 9999)}"
        file_path = self.repo_path / unique_file_name
        
        file_path.write_text(unique_content, encoding="utf-8")

        monitor = RepoMonitor(str(self.repo_path))
        status_output = monitor.check_status()
        self.assertIn(unique_file_name, status_output)

        summarizer = RepoSummarizer(str(self.repo_path))
        summary_text = summarizer.generate_summary()
        self.assertIsInstance(summary_text, str)

        reporter = RepoReporter(str(self.repo_path))
        report_filename = f"report_{uuid.uuid4()}.md"
        report_path = self.repo_path / report_filename
        
        generated_report = reporter.generate_report(status_output, summary_text, str(report_path))
        self.assertTrue(Path(generated_report).exists())

        backup_module = RepoBackup(str(self.repo_path))
        backup_success = backup_module.create_backup()
        self.assertTrue(backup_success)

        log_event_msg = f"Logged event {uuid.uuid4()}"
        logged = self.logger.log_event(log_event_msg)
        self.assertTrue(logged)


if __name__ == "__main__":
    unittest.main()