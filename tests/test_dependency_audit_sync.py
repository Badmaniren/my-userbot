import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.dependency_audit_sync import DependencyAuditSync

class TestDependencyAuditSync(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.branch = "".join(random.choices(string.ascii_lowercase, k=8))
        self.stream_source = f"https://{uuid.uuid4().hex}.com/repo"
        self.audit_sync = DependencyAuditSync(self.repo_path)

    def test_execute_audit_and_sync_flow(self):
        # Генерируем случайные данные для проверки
        report_name = f"report_{uuid.uuid4().hex}.json"
        cve_id = f"CVE-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        target_ver = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        
        with patch('skills.dependency_audit_sync.dependency_audit_aggregator') as mock_aggregator, \
             patch('skills.dependency_audit_sync.repo_sync') as mock_sync:
            
            # Настройка моков
            mock_aggregator.start_new.return_value = {"status": "success", "id": uuid.uuid4().hex}
            mock_aggregator.aggregate_dependencies.return_value = f"Audit result for {cve_id}"
            
            mock_sync_instance = MagicMock()
            mock_sync_instance.synchronize.return_value = True
            mock_sync.RepoSync.return_value = mock_sync_instance
            
            # Выполнение
            result = self.audit_sync.run_full_cycle(self.branch, self.stream_source, report_name, cve_id, target_ver)
            
            # Проверки
            self.assertTrue(result)
            mock_aggregator.start_new.assert_called_with(self.repo_path, self.branch, self.stream_source)
            mock_aggregator.aggregate_dependencies.assert_called_with(self.repo_path, report_name, cve_id, target_ver)
            mock_sync_instance.synchronize.assert_called_once()

    def test_repo_monitor_integration(self):
        expected_status = f"STATUS_{uuid.uuid4().hex.upper()}"
        
        with patch('skills.dependency_audit_sync.repo_sync') as mock_sync:
            mock_monitor = MagicMock()
            mock_monitor.check_status.return_value = expected_status
            mock_sync.RepoMonitor.return_value = mock_monitor
            
            status = self.audit_sync.get_repo_health()
            
            self.assertEqual(status, expected_status)
            mock_sync.RepoMonitor.assert_called_with(self.repo_path)

    def test_auto_commit_failure_handling(self):
        # Генерируем случайный ID для проверки логирования
        event_id = uuid.uuid4().hex
        
        with patch('skills.dependency_audit_sync.repo_sync') as mock_sync:
            mock_committer = MagicMock()
            mock_committer.process_and_commit.return_value = False
            mock_sync.RepoAutoCommitter.return_value = mock_committer
            
            mock_logger = MagicMock()
            mock_sync.RepoLogger.return_value = mock_logger
            
            result = self.audit_sync.attempt_commit(event_id)
            
            self.assertFalse(result)
            mock_logger.log_event.assert_called_with("commit_failed", event_id)

    def test_report_saving_with_random_content(self):
        random_content = f"Data: {uuid.uuid4().hex} | Random: {random.random()}"
        report_path = f"/tmp/{uuid.uuid4().hex}.txt"
        
        with patch('skills.dependency_audit_sync.repo_sync') as mock_sync:
            mock_reporter = MagicMock()
            mock_reporter.save_report.return_value = True
            mock_sync.RepoReporter.return_value = mock_reporter
            
            success = self.audit_sync.save_audit_report(report_path, random_content)
            
            self.assertTrue(success)
            mock_reporter.save_report.assert_called_with(report_path, random_content)

    def test_sync_initialization_parameters(self):
        # Проверка передачи пути в конструктор RepoSync
        with patch('skills.dependency_audit_sync.repo_sync') as mock_sync:
            self.audit_sync.synchronize_now()
            
            mock_sync.RepoSync.assert_called_with(self.repo_path)
            mock_sync.RepoSync.return_value.synchronize.assert_called_once()

if __name__ == '__main__':
    unittest.main()