import io
import os
import random
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = os.path.join(
            "/tmp", f"repo_{uuid.uuid4().hex[:8]}"
        )
        with patch("skills.repo_health_dispatcher.RepoHealthDashboard"), \
             patch("skills.repo_health_dispatcher.RepoNotifier"):
            self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def test_notify_with_retry_success_on_first_try(self):
        mock_notify = MagicMock(return_value=True)
        result = self.dispatcher._notify_with_retry(mock_notify)
        self.assertTrue(result)
        mock_notify.assert_called_once()

    def test_notify_with_retry_success_after_retries(self):
        mock_notify = MagicMock(side_effect=[False, False, True])
        result = self.dispatcher._notify_with_retry(mock_notify)
        self.assertTrue(result)
        self.assertEqual(mock_notify.call_count, 3)

    def test_notify_with_retry_failure(self):
        mock_notify = MagicMock(return_value=False)
        result = self.dispatcher._notify_with_retry(mock_notify)
        self.assertFalse(result)
        self.assertEqual(mock_notify.call_count, 3)

    def test_dispatch_health_and_notify_success(self):
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")
        
        with patch.object(self.dispatcher.repo_health_dashboard, "generate_dashboard") as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=True) as mock_export, \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_retry:

            result = self.dispatcher.dispatch_health_and_notify(file_path)

            self.assertTrue(result)
            mock_gen.assert_called_once()
            mock_export.assert_called_once_with(file_path)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify, file_path)

    def test_dispatch_health_and_notify_export_fail(self):
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")
        
        with patch.object(self.dispatcher.repo_health_dashboard, "generate_dashboard") as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=False) as mock_export, \
             patch.object(self.dispatcher, "_notify_with_retry") as mock_retry:

            result = self.dispatcher.dispatch_health_and_notify(file_path)

            self.assertFalse(result)
            mock_gen.assert_called_once()
            mock_export.assert_called_once_with(file_path)
            mock_retry.assert_not_called()

    def test_process_stream_and_dispatch_with_string(self):
        raw_stream_str = f"stream_data_{uuid.uuid4().hex}"
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")

        with patch.object(self.dispatcher.repo_health_dashboard, "process_stream") as mock_process, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard") as mock_export, \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_retry:

            result = self.dispatcher.process_stream_and_dispatch(raw_stream_str, file_path)

            self.assertTrue(result)
            mock_process.assert_called_once()
            called_arg = mock_process.call_args[0][0]
            self.assertIsInstance(called_arg, io.BytesIO)
            self.assertEqual(called_arg.read(), raw_stream_str.encode("utf-8"))
            mock_export.assert_called_once_with(file_path)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify, file_path)

    def test_process_stream_and_dispatch_with_bytesio(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")

        with patch.object(self.dispatcher.repo_health_dashboard, "process_stream") as mock_process, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard") as mock_export, \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_retry:

            result = self.dispatcher.process_stream_and_dispatch(stream, file_path)

            self.assertTrue(result)
            mock_process.assert_called_once_with(stream)
            mock_export.assert_called_once_with(file_path)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify, file_path)

    def test_check_and_notify_critical(self):
        title = f"Title_{uuid.uuid4().hex[:6]}"
        value = random.randint(100, 999)
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.html")
        widget_output = f"<div>{uuid.uuid4().hex}</div>"

        with patch.object(self.dispatcher.repo_health_dashboard, "render_widget", return_value=widget_output) as mock_render, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file_open, \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_retry:

            result = self.dispatcher.check_and_notify_critical(title, value, file_path)

            self.assertTrue(result)
            mock_render.assert_called_once_with(title, value)
            mock_file_open.assert_called_once_with(file_path, "w", encoding="utf-8")
            mock_file_open().write.assert_called_once_with(widget_output)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify_and_commit)

    def test_dispatch(self):
        expected_report_path = os.path.join(self.repo_path, "report.json")

        with patch.object(self.dispatcher, "dispatch_health_and_notify", return_value=True) as mock_dispatch_hn:
            result = self.dispatcher.dispatch()

            self.assertTrue(result)
            mock_dispatch_hn.assert_called_once_with(expected_report_path)


if __name__ == "__main__":
    unittest.main()