import io
import os
import random
import unittest
from unittest.mock import patch, MagicMock
import uuid
import string

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"

    def test_init(self):
        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dashboard, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notifier:
            
            dispatcher = RepoHealthDispatcher(self.repo_path)
            
            self.assertEqual(dispatcher.repo_path, self.repo_path)
            mock_dashboard.assert_called_once_with(self.repo_path)
            mock_notifier.assert_called_once_with(self.repo_path)

    def test_notify_with_retry_success_on_first(self):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        mock_func = MagicMock(return_value=True)
        arg1 = uuid.uuid4().hex
        kwarg1 = uuid.uuid4().hex

        result = dispatcher._notify_with_retry(mock_func, arg1, custom_kwarg=kwarg1)

        self.assertTrue(result)
        mock_func.assert_called_once_with(arg1, custom_kwarg=kwarg1)

    def test_notify_with_retry_success_after_failures(self):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        mock_func = MagicMock(side_effect=[Exception(uuid.uuid4().hex), Exception(uuid.uuid4().hex), True])

        result = dispatcher._notify_with_retry(mock_func)

        self.assertTrue(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_notify_with_retry_all_fails(self):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        mock_func = MagicMock(side_effect=Exception(uuid.uuid4().hex))

        result = dispatcher._notify_with_retry(mock_func)

        self.assertFalse(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_dispatch_health_and_notify_success(self):
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")
        dispatcher = RepoHealthDispatcher(self.repo_path)

        with patch.object(dispatcher.repo_health_dashboard, "generate_dashboard") as mock_gen, \
             patch.object(dispatcher.repo_health_dashboard, "export_dashboard", return_value=True) as mock_export, \
             patch.object(dispatcher, "_notify_with_retry", return_value=True) as mock_notify:

            result = dispatcher.dispatch_health_and_notify(file_path)

            self.assertTrue(result)
            mock_gen.assert_called_once()
            mock_export.assert_called_once_with(file_path)
            mock_notify.assert_called_once_with(dispatcher.repo_notifier.notify, file_path)

    def test_dispatch_health_and_notify_export_fail(self):
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")
        dispatcher = RepoHealthDispatcher(self.repo_path)

        with patch.object(dispatcher.repo_health_dashboard, "generate_dashboard") as mock_gen, \
             patch.object(dispatcher.repo_health_dashboard, "export_dashboard", return_value=False) as mock_export, \
             patch.object(dispatcher, "_notify_with_retry") as mock_notify:

            result = dispatcher.dispatch_health_and_notify(file_path)

            self.assertFalse(result)
            mock_gen.assert_called_once()
            mock_export.assert_called_once_with(file_path)
            mock_notify.assert_not_called()

    def test_process_stream_and_dispatch_with_string(self):
        stream_data = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")
        dispatcher = RepoHealthDispatcher(self.repo_path)

        with patch.object(dispatcher.repo_health_dashboard, "process_stream") as mock_process, \
             patch.object(dispatcher.repo_health_dashboard, "export_dashboard", return_value=True) as mock_export, \
             patch.object(dispatcher, "_notify_with_retry", return_value=True) as mock_notify:

            result = dispatcher.process_stream_and_dispatch(stream_data, file_path)

            self.assertTrue(result)
            mock_process.assert_called_once()
            args, _ = mock_process.call_args
            self.assertIsInstance(args[0], io.BytesIO)
            self.assertEqual(args[0].getvalue(), stream_data.encode("utf-8"))
            mock_export.assert_called_once_with(file_path)
            mock_notify.assert_called_once_with(dispatcher.repo_notifier.notify, file_path)

    def test_process_stream_and_dispatch_with_bytes_io(self):
        stream_bytes = io.BytesIO(uuid.uuid4().hex.encode("utf-8"))
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")
        dispatcher = RepoHealthDispatcher(self.repo_path)

        with patch.object(dispatcher.repo_health_dashboard, "process_stream") as mock_process, \
             patch.object(dispatcher.repo_health_dashboard, "export_dashboard", return_value=True) as mock_export, \
             patch.object(dispatcher, "_notify_with_retry", return_value=True) as mock_notify:

            result = dispatcher.process_stream_and_dispatch(stream_bytes, file_path)

            self.assertTrue(result)
            mock_process.assert_called_once_with(stream_bytes)
            mock_export.assert_called_once_with(file_path)
            mock_notify.assert_called_once_with(dispatcher.repo_notifier.notify, file_path)

    def test_check_and_notify_critical(self):
        title = uuid.uuid4().hex
        value = random.randint(1, 1000)
        file_path = os.path.join(self.repo_path, uuid.uuid4().hex, f"{uuid.uuid4().hex}.txt")
        widget_content = uuid.uuid4().hex
        dispatcher = RepoHealthDispatcher(self.repo_path)

        with patch.object(dispatcher.repo_health_dashboard, "render_widget", return_value=widget_content) as mock_render, \
             patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file_open, \
             patch("os.makedirs") as mock_makedirs, \
             patch.object(dispatcher, "_notify_with_retry", return_value=True) as mock_notify:

            result = dispatcher.check_and_notify_critical(title, value, file_path)

            self.assertTrue(result)
            mock_render.assert_called_once_with(title, value)
            mock_makedirs.assert_called_once_with(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            mock_file_open.assert_called_once_with(file_path, "w", encoding="utf-8")
            mock_file_open().write.assert_called_once_with(widget_content)
            mock_notify.assert_called_once_with(dispatcher.repo_notifier.notify_and_commit)

    def test_dispatch(self):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        expected_path = os.path.join(self.repo_path, "report.json")

        with patch.object(dispatcher, "dispatch_health_and_notify", return_value=True) as mock_dispatch_fn:
            result = dispatcher.dispatch()

            self.assertTrue(result)
            mock_dispatch_fn.assert_called_once_with(expected_path)


if __name__ == "__main__":
    unittest.main()