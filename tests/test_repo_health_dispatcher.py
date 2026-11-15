import io
import os
import random
import string
import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid4().hex}"
        self.file_path = os.path.join(self.repo_path, f"{uuid4().hex}.json")
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def test_init_sets_paths_and_components(self):
        rand_path = f"/opt/repo_{uuid4().hex}"
        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dash, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notif:
            
            dispatcher = RepoHealthDispatcher(rand_path)
            self.assertEqual(dispatcher.repo_path, rand_path)
            mock_dash.assert_called_once_with(rand_path)
            mock_notif.assert_called_once_with(rand_path)

    def test_notify_with_retry_success_on_first_try(self):
        mock_func = MagicMock(return_value=True)
        result = self.dispatcher._notify_with_retry(mock_func)
        self.assertTrue(result)
        mock_func.assert_called_once()

    def test_notify_with_retry_success_on_subsequent_try(self):
        mock_func = MagicMock(side_effect=[False, False, True])
        result = self.dispatcher._notify_with_retry(mock_func)
        self.assertTrue(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_notify_with_retry_exhausts_retries(self):
        mock_func = MagicMock(return_value=False)
        result = self.dispatcher._notify_with_retry(mock_func)
        self.assertFalse(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_dispatch_health_and_notify_success(self):
        target_file = os.path.join(self.repo_path, f"{uuid4().hex}.json")
        with patch.object(self.dispatcher.repo_health_dashboard, "generate_dashboard") as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=True) as mock_exp, \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_notify:

            res = self.dispatcher.dispatch_health_and_notify(target_file)
            self.assertTrue(res)
            mock_gen.assert_called_once()
            mock_exp.assert_called_once_with(target_file)
            mock_notify.assert_called_once_with(self.dispatcher.repo_notifier.notify, target_file)

    def test_dispatch_health_and_notify_export_failure(self):
        target_file = os.path.join(self.repo_path, f"{uuid4().hex}.json")
        with patch.object(self.dispatcher.repo_health_dashboard, "generate_dashboard"), \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=False), \
             patch.object(self.dispatcher, "_notify_with_retry") as mock_notify:

            res = self.dispatcher.dispatch_health_and_notify(target_file)
            self.assertFalse(res)
            mock_notify.assert_not_called()

    def test_process_stream_and_dispatch_with_string(self):
        random_str_content = uuid4().hex
        target_file = os.path.join(self.repo_path, f"{uuid4().hex}.json")

        with patch.object(self.dispatcher.repo_health_dashboard, "process_stream") as mock_process, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=True), \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True):

            res = self.dispatcher.process_stream_and_dispatch(random_str_content, target_file)
            self.assertTrue(res)
            mock_process.assert_called_once()
            passed_stream = mock_process.call_args[0][0]
            self.assertIsInstance(passed_stream, io.BytesIO)
            self.assertEqual(passed_stream.read().decode("utf-8"), random_str_content)

    def test_process_stream_and_dispatch_with_bytes_io(self):
        random_bytes_content = uuid4().hex.encode("utf-8")
        stream = io.BytesIO(random_bytes_content)
        target_file = os.path.join(self.repo_path, f"{uuid4().hex}.json")

        with patch.object(self.dispatcher.repo_health_dashboard, "process_stream") as mock_process, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=True), \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True):

            res = self.dispatcher.process_stream_and_dispatch(stream, target_file)
            self.assertTrue(res)
            mock_process.assert_called_once_with(stream)

    def test_check_and_notify_critical(self):
        title = f"alert_{uuid4().hex}"
        value = random.randint(100, 999)
        target_file = os.path.join(self.repo_path, f"{uuid4().hex}.log")
        rendered_widget = f"WIDGET::{uuid4().hex}"

        with patch.object(self.dispatcher.repo_health_dashboard, "render_widget", return_value=rendered_widget) as mock_render, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file_open, \
             patch.object(self.dispatcher, "_notify_with_retry", return_value=True) as mock_notify:

            res = self.dispatcher.check_and_notify_critical(title, value, target_file)
            self.assertTrue(res)
            mock_render.assert_called_once_with(title, value)
            mock_file_open.assert_called_once_with(target_file, "w", encoding="utf-8")
            mock_file_open().write.assert_called_once_with(rendered_widget)
            mock_notify.assert_called_once_with(self.dispatcher.repo_notifier.notify_and_commit)

    def test_dispatch(self):
        expected_report_path = os.path.join(self.repo_path, "report.json")
        with patch.object(self.dispatcher, "dispatch_health_and_notify", return_value=True) as mock_dispatch_method:
            res = self.dispatcher.dispatch()
            self.assertTrue(res)
            mock_dispatch_method.assert_called_once_with(expected_report_path)


if __name__ == "__main__":
    unittest.main()