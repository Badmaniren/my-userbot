import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.repo_sync import start_new


class TestRepoSyncStartNew(unittest.TestCase):

    def test_start_new_execution_flow(self):
        rand_repo_path = f"/tmp/{uuid.uuid4().hex}"
        rand_message = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        rand_status = f"status_{uuid.uuid4().hex[:8]}"

        with patch('skills.repo_sync.RepoMonitor') as mock_monitor_cls, \
             patch('skills.repo_sync.RepoAutoCommitter') as mock_committer_cls, \
             patch('skills.repo_sync.RepoReporter') as mock_reporter_cls:

            mock_monitor_instance = mock_monitor_cls.return_value
            mock_monitor_instance.check_status.return_value = rand_status

            mock_committer_instance = mock_committer_cls.return_value
            mock_committer_instance.run.return_value = True

            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.generate_final_report.return_value = rand_message

            result = start_new(rand_repo_path)

            mock_monitor_cls.assert_called_once_with(rand_repo_path)
            mock_monitor_instance.check_status.assert_called_once()

            mock_committer_cls.assert_called_once_with(rand_repo_path)
            mock_committer_instance.run.assert_called_once()

            mock_reporter_cls.assert_called_once_with(rand_repo_path)
            mock_reporter_instance.generate_final_report.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertIn("status", result)
            self.assertEqual(result["status"], rand_status)
            self.assertIn("report", result)
            self.assertEqual(result["report"], rand_message)

    def test_start_new_failure_handling(self):
        rand_repo_path = f"/var/repo/{uuid.uuid4().hex}"

        with patch('skills.repo_sync.RepoMonitor') as mock_monitor_cls:
            mock_monitor_instance = mock_monitor_cls.return_value
            mock_monitor_instance.check_status.side_effect = Exception(uuid.uuid4().hex)

            with self.assertRaises(Exception):
                start_new(rand_repo_path)

            mock_monitor_cls.assert_called_once_with(rand_repo_path)
            mock_monitor_instance.check_status.assert_called_once()