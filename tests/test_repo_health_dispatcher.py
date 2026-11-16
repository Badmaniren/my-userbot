import io
import os
import random
import unittest
from unittest.mock import MagicMock, patch
import uuid
from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = os.path.join("/tmp", uuid.uuid4().hex)
        self.file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")
        self.title = uuid.uuid4().hex
        self.value = random.randint(1, 1000)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_init_sets_paths_and_components(self, mock_notifier, mock_dashboard):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        self.assertEqual(dispatcher.repo_path, self.repo_path)
        mock_dashboard.assert_called_once_with(self.repo_path)
        mock_notifier.assert_called_once_with(self.repo_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_notify_with_retry_success_on_first_try(self, mock_dashboard, mock_notifier):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        notify_func = MagicMock(return_value=True)

        result = dispatcher._notify_with_retry(notify_func, self.file_path)

        self.assertTrue(result)
        notify_func.assert_called_once_with(self.file_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_notify_with_retry_success_on_last_try(self, mock_dashboard, mock_notifier):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        notify_func = MagicMock(side_effect=[False, False, True])

        result = dispatcher._notify_with_retry(notify_func, self.file_path)

        self.assertTrue(result)
        self.assertEqual(notify_func.call_count, 3)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_notify_with_retry_all_fails(self, mock_dashboard, mock_notifier):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        notify_func = MagicMock(return_value=False)

        result = dispatcher._notify_with_retry(notify_func, self.file_path)

        self.assertFalse(result)
        self.assertEqual(notify_func.call_count, 3)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch_health_and_notify_success(self, mock_dashboard, mock_notifier):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=True)
        dispatcher._notify_with_retry = MagicMock(return_value=True)

        result = dispatcher.dispatch_health_and_notify(self.file_path)

        self.assertTrue(result)
        dispatcher.repo_health_dashboard.generate_dashboard.assert_called_once()
        dispatcher.repo_health_dashboard.export_dashboard.assert_called_once_with(self.file_path)
        dispatcher._notify_with_retry.assert_called_once_with(dispatcher.repo_notifier.notify, self.file_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch_health_and_notify_export_fails(self, mock_dashboard, mock_notifier):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=False)
        dispatcher._notify_with_retry = MagicMock()

        result = dispatcher.dispatch_health_and_notify(self.file_path)

        self.assertFalse(result)
        dispatcher.repo_health_dashboard.generate_dashboard.assert_called_once()
        dispatcher.repo_health_dashboard.export_dashboard.assert_called_once_with(self.file_path)
        dispatcher._notify_with_retry.assert_not_called()

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_process_stream_and_dispatch_with_string_data(self, mock_dashboard, mock_notifier):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        random_string = uuid.uuid4().hex
        dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=True)
        dispatcher._notify_with_retry = MagicMock(return_value=True)

        result = dispatcher.process_stream_and_dispatch(random_string, self.file_path)

        self.assertTrue(result)
        dispatcher.repo_health_dashboard.process_stream.assert_called_once()
        args, _ = dispatcher.repo_health_dashboard.process_stream.call_args
        self.assertIsInstance(args[0], io.BytesIO)
        self.assertEqual(args[0].read().decode("utf-8"), random_string)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_process_stream_and_dispatch_with_bytes_io_data(self, mock_dashboard, mock_notifier):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        random_bytes = io.BytesIO(uuid.uuid4().hex.encode("utf-8"))
        dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=True)
        dispatcher._notify_with_retry = MagicMock(return_value=True)

        result = dispatcher.process_stream_and_dispatch(random_bytes, self.file_path)

        self.assertTrue(result)
        dispatcher.repo_health_dashboard.process_stream.assert_called_once_with(random_bytes)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_check_and_notify_critical_writes_and_notifies(self, mock_dashboard, mock_notifier):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        rendered_content = uuid.uuid4().hex
        dispatcher.repo_health_dashboard.render_widget = MagicMock(return_value=rendered_content)
        dispatcher._notify_with_retry = MagicMock(return_value=True)

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            result = dispatcher.check_and_notify_critical(self.title, self.value, self.file_path)

            self.assertTrue(result)
            dispatcher.repo_health_dashboard.render_widget.assert_called_once_with(self.title, self.value)
            mock_file.assert_called_once_with(self.file_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(rendered_content)
            dispatcher._notify_with_retry.assert_called_once_with(dispatcher.repo_notifier.notify_and_commit)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch_calls_dispatch_health_and_notify_with_expected_path(self, mock_dashboard, mock_notifier):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        expected_path = os.path.join(self.repo_path, "report.json")
        dispatcher.dispatch_health_and_notify = MagicMock(return_value=True)

        result = dispatcher.dispatch()

        self.assertTrue(result)
        dispatcher.dispatch_health_and_notify.assert_called_once_with(expected_path)


if __name__ == "__main__":
    unittest.main()