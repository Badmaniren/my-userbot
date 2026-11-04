import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.repo_recovery import RepoRecovery


class TestRepoRecovery(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.backup_path = f"/tmp/backup_{uuid.uuid4().hex}"
        self.event_name = f"event_{uuid.uuid4().hex}"
        self.event_details = f"details_{uuid.uuid4().hex}"
        self.error_code = f"ERR_{random.randint(1000, 9999)}"
        self.error_msg = f"msg_{uuid.uuid4().hex}"

    def test_recovery_success_composition(self):
        with patch('skills.repo_recovery.RepoBackup') as mock_backup_cls, \
             patch('skills.repo_recovery.RepoLogger') as mock_logger_cls:
            
            mock_backup_instance = mock_backup_cls.return_value
            mock_backup_instance.backup.return_value = True

            mock_logger_instance = mock_logger_cls.return_value
            mock_logger_instance.log_event.return_value = True

            recovery = RepoRecovery(self.repo_path)
            result = recovery.recover_repository()

            self.assertTrue(result)
            mock_backup_cls.assert_called_once_with(self.repo_path)
            mock_backup_instance.backup.assert_called_once()
            mock_logger_cls.assert_called_once_with(self.repo_path)
            mock_logger_instance.log_event.assert_called()

    def test_recovery_backup_failure_logs_error(self):
        with patch('skills.repo_recovery.RepoBackup') as mock_backup_cls, \
             patch('skills.repo_recovery.RepoLogger') as mock_logger_cls:
            
            mock_backup_instance = mock_backup_cls.return_value
            mock_backup_instance.backup.return_value = False

            mock_logger_instance = mock_logger_cls.return_value
            mock_logger_instance.log_error.return_value = None

            recovery = RepoRecovery(self.repo_path)
            result = recovery.recover_repository()

            self.assertFalse(result)
            mock_backup_instance.backup.assert_called_once()
            mock_logger_instance.log_error.assert_called_once()

    def test_safe_restore_execution(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes)
        
        with patch('skills.repo_recovery.RepoBackup') as mock_backup_cls, \
             patch('skills.repo_recovery.RepoLogger') as mock_logger_cls:
            
            mock_backup_instance = mock_backup_cls.return_value
            mock_backup_instance.create_backup.return_value = True

            mock_logger_instance = mock_logger_cls.return_value
            mock_logger_instance.process_log_stream.return_value = True

            recovery = RepoRecovery(self.repo_path)
            result = recovery.safe_restore(stream_data)

            self.assertTrue(result)
            mock_backup_instance.create_backup.assert_called_once()
            mock_logger_instance.process_log_stream.assert_called_once_with(stream_data)


if __name__ == '__main__':
    unittest.main()