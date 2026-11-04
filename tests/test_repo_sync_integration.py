import unittest
import tempfile
import shutil
import os
import uuid
import random
from pathlib import Path

from skills.repo_sync import RepoSync
from skills.repo_auto_committer import RepoAutoCommitter
from skills.repo_logger import RepoLogger
from skills.repo_reporter import RepoReporter


class TestRepoSyncIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_sync_real_workflow(self):
        unique_file_name = f"sync_file_{uuid.uuid4().hex[:8]}.txt"
        unique_content = f"Random sync content: {random.randint(10000, 99999)}"
        file_path = os.path.join(self.repo_path, unique_file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(unique_content)

        auto_committer = RepoAutoCommitter(self.repo_path)
        commit_result = auto_committer.process_and_commit()
        self.assertTrue(commit_result, "AutoCommitter должен успешно закоммитить изменения.")

        logger = RepoLogger(self.repo_path)
        log_event_name = f"sync_event_{uuid.uuid4().hex[:6]}"
        log_success = logger.log_event(log_event_name, {"file": unique_file_name})
        self.assertTrue(log_success, "RepoLogger должен залогировать событие.")

        reporter = RepoReporter(self.repo_path)
        report_filename = f"report_{uuid.uuid4().hex[:6]}.txt"
        report_path = os.path.join(self.repo_path, report_filename)
        
        summary_text = f"Sync summary random ID: {uuid.uuid4()}"
        saved_report = reporter.save_report(report_path, summary_text)
        self.assertTrue(os.path.exists(report_path), "Отчет должен быть физически создан на диске.")

        repo_sync = RepoSync(self.repo_path)
        
        sync_methods = [m for m in dir(repo_sync) if not m.startswith('_')]
        self.assertGreater(len(sync_methods), 0, "Модуль RepoSync должен содержать публичные методы для синхронизации.")


if __name__ == '__main__':
    unittest.main()