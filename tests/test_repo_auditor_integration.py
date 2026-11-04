import os
import random
import shutil
import subprocess
import tempfile
import unittest
import uuid

from skills.git_committer import GitCommitter
from skills.repo_auditor import RepoAuditor
from skills.repo_logger import RepoLogger
from skills.repo_monitor import RepoMonitor
from skills.repo_reporter import RepoReporter
from skills.repo_summarizer import RepoSummarizer


class TestRepoAuditorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.temp_dir, f"repo_{uuid.uuid4().hex[:8]}")
        os.makedirs(self.repo_path, exist_ok=True)

        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "AuditTester"], cwd=self.repo_path, check=True)
        subprocess.run(["git", "config", "user.email", "audittester@example.com"], cwd=self.repo_path, check=True)

        self.random_token = f"token_{uuid.uuid4().hex}"
        self.test_files = []

        for i in range(random.randint(2, 4)):
            fname = f"sample_{i}_{uuid.uuid4().hex[:6]}.py"
            fpath = os.path.join(self.repo_path, fname)
            content = f"# Audit Test File {i}\n# Token: {self.random_token}\ndef calculate_{i}():\n    return {random.randint(1000, 9999)}\n"
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            self.test_files.append(fpath)

        committer = GitCommitter(self.repo_path)
        committer.commit_changes(self.test_files[0], f"Initial commit with token {self.random_token}")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_repo_auditor_integration_with_repo_skills(self):
        auditor = RepoAuditor(self.repo_path)

        audit_fn = None
        for name in ["audit", "audit_repository", "run_audit", "perform_audit", "run"]:
            if hasattr(auditor, name) and callable(getattr(auditor, name)):
                audit_fn = getattr(auditor, name)
                break

        self.assertIsNotNone(audit_fn, "RepoAuditor should implement an auditing method")
        audit_result = audit_fn()
        self.assertIsNotNone(audit_result)

        logger = RepoLogger(self.repo_path)
        logger.log_event("audit_run", {"token": self.random_token})
        logger.log_metric("audit_files_count", len(self.test_files))

        monitor = RepoMonitor(self.repo_path)
        status = monitor.check_status()
        self.assertIsInstance(status, str)

        summarizer = RepoSummarizer(self.repo_path)
        summary = summarizer.generate_summary()
        self.assertIsInstance(summary, str)

        reporter = RepoReporter(self.repo_path)
        out_report_path = os.path.join(self.repo_path, f"report_{uuid.uuid4().hex[:6]}.txt")
        report_content = f"Audit summary: {summary}\nStatus: {status}\nToken: {self.random_token}"
        reporter.save_report(out_report_path, report_content)

        self.assertTrue(os.path.exists(out_report_path))
        with open(out_report_path, "r", encoding="utf-8") as f:
            read_data = f.read()
        self.assertIn(self.random_token, read_data)


if __name__ == "__main__":
    unittest.main()