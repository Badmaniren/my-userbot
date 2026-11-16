import io
import logging
import os
import random
import string
import unittest
from unittest.mock import patch, MagicMock
import uuid

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = os.path.join(
            "/tmp", f"repo_{uuid.uuid4().hex[:8]}"
        )
        self.dispatcher = RepoHealthDispatcher(self.random_repo_path)

    def test_init_sets_paths_and_components(self):
        self.assertEqual(self.dispatcher.repo_path, self.random_repo_path)
        self.assertIsNotNone(self.dispatcher.repo_health_dashboard)
        self.assertIsNotNone(self.dispatcher.repo_notifier)

    def test_notify_with_retry_success_on_first_attempt(self):
        target_value = random.choice([True, "success"])
        mock_func = MagicMock(return_value=target_value)
        
        arg1 = uuid.uuid4().hex
        arg2 = random.randint(100, 999)

        result = self.dispatcher._notify_with_retry(mock_func, arg1, kwarg_key=arg2)
        
        self.assertTrue(result)
        mock_func.assert_called_once_with(arg1, kwarg_key=arg2)

    def test_notify_with_retry_success_after_failures(self):
        mock_func = MagicMock(side_effect=[Exception(uuid.uuid4().hex), Exception(uuid.uuid4().hex), True])
        
        arg1 = uuid.uuid4().hex

        result = self.dispatcher._notify_with_retry(mock_func, arg1)
        
        self.assertTrue(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_notify_with_retry_exhausted_retries(self):
        err_msg = uuid.uuid4().hex
        mock_func = MagicMock(side_effect=Exception(err_msg))

        with self.assertLogs(level='ERROR') as log:
            result = self.dispatcher._notify_with_retry(mock_func)
            
        self.assertFalse(result)
        self.assertEqual(mock_func.call_count, 3)
        self.assertTrue(any(err_msg in message for message in log.output))

    def test_dispatch_health_and_notify_success(self):
        random_file_path = os.path.join(self.random_repo_path, f"{uuid.uuid4().hex}.json")

        with patch.object(self.dispatcher.repo_health_dashboard, 'generate_dashboard') as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, 'export_dashboard', return_value=True) as mock_export, \
             patch.object(self.dispatcher.repo_notifier, 'notify', return_value=True) as mock_notify:

            result = self.dispatcher.dispatch_health_and_notify(random_file_path)

            self.assertTrue(result)
            mock_gen.assert_called_once()
            mock_export.assert_called_once_with(random_file_path)
            mock_notify.assert_called_once_with(random_file_path)

    def test_dispatch_health_and_notify_export_failure(self):
        random_file_path = os.path.join(self.random_repo_path, f"{uuid.uuid4().hex}.json")

        with patch.object(self.dispatcher.repo_health_dashboard, 'generate_dashboard') as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, 'export