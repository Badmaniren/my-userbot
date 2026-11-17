import unittest
import io
import os
import uuid
import random
from unittest.mock import MagicMock, patch, mock_open
from skills.repo_health_dispatcher import RepoHealthDispatcher

class TestRepoHealthDispatcher(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def test_notify_with_retry_success_on_first(self):
        mock_func = MagicMock(return_value=True)
        result = self.dispatcher._notify_with_retry(mock_func, "arg1")
        self.assertTrue(result)
        self.assertEqual(mock_func.call_count, 1)

    def test_notify_with_retry_exhausts_retries(self):
        mock_func = MagicMock(side_effect=Exception("Random failure"))
        result = self.dispatcher._notify_with_retry(mock_func, "arg1")
        self.assertFalse(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_dispatch_health_and_notify_flow(self):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        with patch.object(self.dispatcher.repo_health_dashboard, 'generate_dashboard') as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, 'export_dashboard', return_value=True), \
             patch.object(self.dispatcher, '_notify_with_retry', return_value=True) as mock_retry:
            
            result = self.dispatcher.dispatch_health_and_notify(file_path)
            self.assertTrue(result)
            mock_gen.assert_called_once()
            mock_retry.assert_called_once()

    def test_process_stream_and_dispatch_with_bytes(self):
        random_data = uuid.uuid4().hex.encode("utf-8")
        stream = io.BytesIO(random_data)
        file_path = f"/{uuid.uuid4().hex}.json"
        
        with patch.object(self.dispatcher.repo_health_dashboard, 'process_stream') as mock_proc, \
             patch.object(self.dispatcher.repo_health_dashboard, 'export_dashboard', return_value=True), \
             patch.object(self.dispatcher, '_notify_with_retry', return_value=True):
            
            result = self.dispatcher.process_stream_and_dispatch(stream, file_path)
            self.assertTrue(result)
            mock_proc.assert_called_with(stream)

    def test_check_and_notify_critical_file_io(self):
        title = uuid.uuid4().hex
        value = random.randint(1, 1000)
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt"
        rendered_content = f"Report: {uuid.uuid4().hex}"
        
        with patch.object(self.dispatcher.repo_health_dashboard, 'render_widget', return_value=rendered_content), \
             patch("os.makedirs"), \
             patch("builtins.open", mock_open()) as mocked_file, \
             patch.object(self.dispatcher.repo_notifier, 'notify_and_commit', return_value=True):
            
            result = self.dispatcher.check_and_notify_critical(title, value, file_path)
            
            self.assertTrue(result)
            mocked_file.assert_called_with(file_path, "w", encoding="utf-8")
            mocked_file().write.assert_called_once_with(rendered_content)

    def test_dispatch_default_path(self):
        with patch.object(self.dispatcher, 'dispatch_health_and_notify', return_value=True) as mock_dispatch:
            result = self.dispatcher.dispatch()
            expected_path = os.path.join(self.repo_path, "report.json")
            
            self.assertTrue(result)
            mock_dispatch.assert_called_with(expected_path)

if __name__ == "__main__":
    unittest.main()