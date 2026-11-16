import unittest
from unittest.mock import MagicMock, patch, mock_open
import io
import os
import uuid
import random
import string
from skills.repo_health_dispatcher import RepoHealthDispatcher

class TestRepoHealthDispatcher(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def test_notify_with_retry_success_on_first_attempt(self):
        mock_func = MagicMock(return_value=True)
        result = self.dispatcher._notify_with_retry(mock_func, "arg1", key="val")
        self.assertTrue(result)
        self.assertEqual(mock_func.call_count, 1)

    def test_notify_with_retry_success_on_last_attempt(self):
        mock_func = MagicMock(side_effect=[False, False, True])
        result = self.dispatcher._notify_with_retry(mock_func)
        self.assertTrue(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_notify_with_retry_exhausts_retries(self):
        mock_func = MagicMock(side_effect=Exception("Critical failure"))
        result = self.dispatcher._notify_with_retry(mock_func)
        self.assertFalse(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_dispatch_health_and_notify_flow(self):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        with patch.object(self.dispatcher.repo_health_dashboard, 'generate_dashboard') as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, 'export_dashboard', return_value=True) as mock_exp, \
             patch.object(self.dispatcher, '_notify_with_retry', return_value=True) as mock_notify:
            
            result = self.dispatcher.dispatch_health_and_notify(file_path)
            
            self.assertTrue(result)
            mock_gen.assert_called_once()
            mock_exp.assert_called_with(file_path)
            mock_notify.assert_called_once()

    def test_process_stream_and_dispatch_with_string(self):
        random_str = ''.join(random.choices(string.ascii_letters, k=20))
        file_path = f"/{uuid.uuid4().hex}.json"
        
        with patch.object(self.dispatcher.repo_health_dashboard, 'process_stream') as mock_proc, \
             patch.object(self.dispatcher.repo_health_dashboard, 'export_dashboard', return_value=True), \
             patch.object(self.dispatcher, '_notify_with_retry', return_value=True):
            
            result = self.dispatcher.process_stream_and_dispatch(random_str, file_path)
            self.assertTrue(result)
            self.assertIsInstance(mock_proc.call_args[0][0], io.BytesIO)

    def test_check_and_notify_critical_file_operations(self):
        title = uuid.uuid4().hex
        value = random.randint(1, 100)
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt"
        content = f"Report: {uuid.uuid4().hex}"
        
        with patch.object(self.dispatcher.repo_health_dashboard, 'render_widget', return_value=content), \
             patch("os.makedirs"), \
             patch("builtins.open", mock_open()) as mocked_file, \
             patch.object(self.dispatcher, '_notify_with_retry', return_value=True):
            
            result = self.dispatcher.check_and_notify_critical(title, value, file_path)
            
            self.assertTrue(result)
            mocked_file.assert_called_with(file_path, "w", encoding="utf-8")
            mocked_file().write.assert_called_once_with(content)

    def test_dispatch_default_path(self):
        with patch.object(self.dispatcher, 'dispatch_health_and_notify', return_value=True) as mock_dispatch:
            result = self.dispatcher.dispatch()
            expected_path = os.path.join(self.repo_path, "report.json")
            mock_dispatch.assert_called_with(expected_path)
            self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()