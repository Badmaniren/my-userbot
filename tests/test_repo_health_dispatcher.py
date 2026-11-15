import io
import os
import random
import unittest
from unittest.mock import MagicMock, patch
import uuid
string = __import__('string')

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        with patch("skills.repo_health_dispatcher.RepoHealthDashboard"), \
             patch("skills.repo_health_dispatcher.RepoNotifier"):
            self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def test_init_sets_paths_and_dependencies(self):
        random_path = f"/var/repo/{uuid.uuid4().hex}"
        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dash, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notif:
            
            disp = RepoHealthDispatcher(random_path)
            self.assertEqual(disp.repo_path, random_path)
            mock_dash.assert_called_once_with(random_path)
            mock_notif.assert_called_once_with(random_path)

    def test_notify_with_retry_success_on_first_try(self):
        mock_func = MagicMock(return_value=True)
        arg1 = uuid.uuid4().hex
        kwarg1 = random.randint(100, 999)

        result = self.dispatcher._notify_with_retry(mock_func, arg1, custom_key=kwarg1)

        self.assertTrue(result)
        mock_func.assert_called_once_with(arg1, custom_key=kwarg1)

    def test_notify_with_retry_success_after_failures(self):
        mock_func = MagicMock(side_effect=[False, False, True])
        arg1 = uuid.uuid4().hex

        result = self.dispatcher._notify_with_retry(mock_func, arg1)

        self.assertTrue(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_notify_with_retry_failure_all_retries(self):
        mock_func = MagicMock(return_value=False)
        arg1 = uuid.uuid4().hex

        result = self.dispatcher._notify_with_retry(mock_func, arg1)

        self.assertFalse(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_dispatch_health_and_notify_success(self):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        self.dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=True)
        
        with patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_retry:
            result = self.dispatcher.dispatch_health_and_notify(file_path)

            self.assertTrue(result)
            self.dispatcher.repo_health_dashboard.generate_dashboard.assert_called_once()
            self.dispatcher.repo_health_dashboard.export_dashboard.assert_called_once_with(file_path)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify, file_path)

    def test_dispatch_health_and_notify_export_fails(self):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        self.dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=False)
        
        with patch.object(self.dispatcher, "_notify_with_retry") as mock_retry:
            result = self.dispatcher.dispatch_health_and_notify(file_path)

            self.assertFalse(result)
            self.dispatcher.repo_health_dashboard.generate_dashboard.assert_called_once()
            self.dispatcher.repo_health_dashboard.export_dashboard.assert_called_once_with(file_path)
            mock_retry.assert_not_called()

    def test_process_stream_and_dispatch_with_string(self):
        stream_content = uuid.uuid4().hex
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        self.dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=True)

        with patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_retry:
            result = self.dispatcher.process_stream_and_dispatch(stream_content, file_path)

            self.assertTrue(result)
            self.dispatcher.repo_health_dashboard.process_stream.assert_called_once()
            call_arg = self.dispatcher.repo_health_dashboard.process_stream.call_args[0][0]
            self.assertIsInstance(call_arg, io.BytesIO)
            self.assertEqual(call_arg.read(), stream_content.encode("utf-8"))
            self.dispatcher.repo_health_dashboard.export_dashboard.assert_called_once_with(file_path)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify, file_path)

    def test_process_stream_and_dispatch_with_bytesio(self):
        random_bytes = uuid.uuid4().hex.encode("utf-8")
        stream_data = io.BytesIO(random_bytes)
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        self.dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=True)

        with patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_retry:
            result = self.dispatcher.process_stream_and_dispatch(stream_data, file_path)

            self.assertTrue(result)
            self.dispatcher.repo_health_dashboard.process_stream.assert_called_once_with(stream_data)
            self.dispatcher.repo_health_dashboard.export_dashboard.assert_called_once_with(file_path)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify, file_path)

    def test_check_and_notify_critical(self):
        title = uuid.uuid4().hex
        value = random.randint(1, 1000)
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt"
        rendered_widget_content = uuid.uuid4().hex

        self.dispatcher.repo_health_dashboard.render_widget = MagicMock(return_value=rendered_widget_content)

        mock_file = MagicMock()
        with patch("builtins.open", mock_file), \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_retry:
            
            result = self.dispatcher.check_and_notify_critical(title, value, file_path)

            self.assertTrue(result)
            self.dispatcher.repo_health_dashboard.render_widget.assert_called_once_with(title, value)
            mock_file.assert_called_once_with(file_path, "w", encoding="utf-8")
            mock_file.return_value.__enter__.return_value.write.assert_called_once_with(rendered_widget_content)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify_and_commit)

    def test_dispatch(self):
        expected_report_name = f"{uuid.uuid4().hex}.json"
        expected_path = os.path.join(self.dispatcher.repo_path, "report.json")

        with patch.object(self.dispatcher, "dispatch_health_and_notify", return_value=True) as mock_dispatch_fn:
            result = self.dispatcher.dispatch()

            self.assertTrue(result)
            mock_dispatch_fn.assert_called_once_with(expected_path)


if __name__ == "__main__":
    unittest.main()