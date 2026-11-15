import io
import os
import random
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):
    def setUp(self):
        self.repo_path = os.path.join("/tmp", uuid.uuid4().hex)
        self.file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def test_init_sets_attributes(self):
        random_repo_path = os.path.join("/opt", uuid.uuid4().hex)
        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dash, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notif:
            
            dispatcher = RepoHealthDispatcher(random_repo_path)
            
            self.assertEqual(dispatcher.repo_path, random_repo_path)
            mock_dash.assert_called_once_with(random_repo_path)
            mock_notif.assert_called_once_with(random_repo_path)

    def test_notify_with_retry_success_on_first_try(self):
        expected_result = random.choice([True, False])
        mock_func = MagicMock(return_value=expected_result)
        arg1 = uuid.uuid4().hex
        arg2 = random.randint(1, 100)

        result = self.dispatcher._notify_with_retry(mock_func, arg1, kwarg_key=arg2)

        self.assertEqual(result, expected_result)
        mock_func.assert_called_once_with(arg1, kwarg_key=arg2)

    def test_notify_with_retry_success_after_retries(self):
        mock_func = MagicMock(side_effect=[False, False, True])
        
        result = self.dispatcher._notify_with_retry(mock_func)

        self.assertTrue(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_notify_with_retry_all_fail(self):
        mock_func = MagicMock(return_value=False)

        result = self.dispatcher._notify_with_retry(mock_func)

        self.assertFalse(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_dispatch_health_and_notify_export_fails(self):
        with patch.object(self.dispatcher.repo_health_dashboard, "generate_dashboard") as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=False) as mock_exp, \
             patch.object(self.dispatcher.repo_notifier, "notify") as mock_notify:

            result = self.dispatcher.dispatch_health_and_notify(self.file_path)

            self.assertFalse(result)
            mock_gen.assert_called_once()
            mock_exp.assert_called_once_with(self.file_path)
            mock_notify.assert_not_called()

    def test_dispatch_health_and_notify_success(self):
        with patch.object(self.dispatcher.repo_health_dashboard, "generate_dashboard") as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=True) as mock_exp, \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_retry:

            result = self.dispatcher.dispatch_health_and_notify(self.file_path)

            self.assertTrue(result)
            mock_gen.assert_called_once()
            mock_exp.assert_called_once_with(self.file_path)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify, self.file_path)

    def test_process_stream_and_dispatch_with_string_stream(self):
        random_content = uuid.uuid4().hex
        with patch.object(self.dispatcher.repo_health_dashboard, "process_stream") as mock_process, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=True) as mock_exp, \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_retry:

            result = self.dispatcher.process_stream_and_dispatch(random_content, self.file_path)

            self.assertTrue(result)
            mock_exp.assert_called_once_with(self.file_path)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify, self.file_path)
            
            called_stream = mock_process.call_args[0][0]
            self.assertIsInstance(called_stream, io.BytesIO)
            self.assertEqual(called_stream.read(), random_content.encode("utf-8"))

    def test_process_stream_and_dispatch_with_bytesio_stream(self):
        random_bytes = uuid.uuid4().hex.encode("utf-8")
        stream = io.BytesIO(random_bytes)
        with patch.object(self.dispatcher.repo_health_dashboard, "process_stream") as mock_process, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=False) as mock_exp:

            result = self.dispatcher.process_stream_and_dispatch(stream, self.file_path)

            self.assertFalse(result)
            mock_exp.assert_called_once_with(self.file_path)
            mock_process.assert_called_once_with(stream)

    def test_check_and_notify_critical(self):
        title = uuid.uuid4().hex
        value = random.randint(100, 999)
        rendered_widget = uuid.uuid4().hex

        with patch.object(self.dispatcher.repo_health_dashboard, "render_widget", return_value=rendered_widget) as mock_render, \
             patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file_open, \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_retry:

            result = self.dispatcher.check_and_notify_critical(title, value, self.file_path)

            self.assertTrue(result)
            mock_render.assert_called_once_with(title, value)
            mock_file_open.assert_called_once_with(self.file_path, "w", encoding="utf-8")
            mock_file_open().write.assert_called_once_with(rendered_widget)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify_and_commit)

    def test_dispatch(self):
        expected_report_path = os.path.join(self.repo_path, "report.json")
        expected_return = random.choice([True, False])

        with patch.object(self.dispatcher, "dispatch_health_and_notify", return_value=expected_return) as mock_dispatch_hn:

            result = self.dispatcher.dispatch()

            self.assertEqual(result, expected_return)
            mock_dispatch_hn.assert_called_once_with(expected_report_path)


if __name__ == "__main__":
    unittest.main()