import io
import os
import random
import string
import unittest
from unittest.mock import MagicMock, patch
import uuid

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.random_file_path = f"{self.random_repo_path}/{uuid.uuid4().hex}.json"
        self.random_title = "".join(random.choices(string.ascii_letters, k=10))
        self.random_value = random.randint(100, 999)
        self.random_stream_data = uuid.uuid4().bytes

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_notify_with_retry_success_on_first_try(self, mock_dashboard_cls, mock_notifier_cls):
        dispatcher = RepoHealthDispatcher(self.random_repo_path)
        mock_func = MagicMock(return_value=True)

        result = dispatcher._notify_with_retry(mock_func, self.random_file_path)

        self.assertTrue(result)
        mock_func.assert_called_once_with(self.random_file_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_notify_with_retry_success_on_last_try(self, mock_dashboard_cls, mock_notifier_cls):
        dispatcher = RepoHealthDispatcher(self.random_repo_path)
        mock_func = MagicMock(side_effect=[False, False, True])

        result = dispatcher._notify_with_retry(mock_func, self.random_file_path)

        self.assertTrue(result)
        self.assertEqual(mock_func.call_count, 3)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_notify_with_retry_failure(self, mock_dashboard_cls, mock_notifier_cls):
        dispatcher = RepoHealthDispatcher(self.random_repo_path)
        mock_func = MagicMock(return_value=False)

        result = dispatcher._notify_with_retry(mock_func, self.random_file_path)

        self.assertFalse(result)
        self.assertEqual(mock_func.call_count, 3)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch_health_and_notify_success(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard_instance = mock_dashboard_cls.return_value
        mock_dashboard_instance.export_dashboard.return_value = True

        mock_notifier_instance = mock_notifier_cls.return_value
        mock_notifier_instance.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.random_repo_path)
        result = dispatcher.dispatch_health_and_notify(self.random_file_path)

        self.assertTrue(result)
        mock_dashboard_instance.generate_dashboard.assert_called_once()
        mock_dashboard_instance.export_dashboard.assert_called_once_with(self.random_file_path)
        mock_notifier_instance.notify.assert_called()

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch_health_and_notify_export_failed(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard_instance = mock_dashboard_cls.return_value
        mock_dashboard_instance.export_dashboard.return_value = False

        dispatcher = RepoHealthDispatcher(self.random_repo_path)
        result = dispatcher.dispatch_health_and_notify(self.random_file_path)

        self.assertFalse(result)
        mock_dashboard_instance.generate_dashboard.assert_called_once()
        mock_dashboard_instance.export_dashboard.assert_called_once_with(self.random_file_path)
        mock_notifier_cls.return_value.notify.assert_not_called()

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_process_stream_and_dispatch_with_string(self, mock_dashboard_cls, mock_notifier_cls):
        random_string_stream = uuid.uuid4().hex
        mock_dashboard_instance = mock_dashboard_cls.return_value
        mock_dashboard_instance.export_dashboard.return_value = True

        mock_notifier_instance = mock_notifier_cls.return_value
        mock_notifier_instance.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.random_repo_path)
        result = dispatcher.process_stream_and_dispatch(random_string_stream, self.random_file_path)

        self.assertTrue(result)
        mock_dashboard_instance.process_stream.assert_called_once()
        # Verify that process_stream received an io.BytesIO stream
        called_arg = mock_dashboard_instance.process_stream.call_args[0][0]
        self.assertIsInstance(called_arg, io.BytesIO)
        self.assertEqual(called_arg.read(), random_string_stream.encode("utf-8"))

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_process_stream_and_dispatch_with_bytes_io(self, mock_dashboard_cls, mock_notifier_cls):
        bytes_stream = io.BytesIO(self.random_stream_data)
        mock_dashboard_instance = mock_dashboard_cls.return_value
        mock_dashboard_instance.export_dashboard.return_value = True

        mock_notifier_instance = mock_notifier_cls.return_value
        mock_notifier_instance.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.random_repo_path)
        result = dispatcher.process_stream_and_dispatch(bytes_stream, self.random_file_path)

        self.assertTrue(result)
        mock_dashboard_instance.process_stream.assert_called_once_with(bytes_stream)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_check_and_notify_critical(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard_instance = mock_dashboard_cls.return_value
        random_widget_output = uuid.uuid4().hex
        mock_dashboard_instance.render_widget.return_value = random_widget_output

        mock_notifier_instance = mock_notifier_cls.return_value
        mock_notifier_instance.notify_and_commit.return_value = True

        dispatcher = RepoHealthDispatcher(self.random_repo_path)

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            result = dispatcher.check_and_notify_critical(self.random_title, self.random_value, self.random_file_path)

            self.assertTrue(result)
            mock_dashboard_instance.render_widget.assert_called_once_with(self.random_title, self.random_value)
            mock_file.assert_called_once_with(self.random_file_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(random_widget_output)
            mock_notifier_instance.notify_and_commit.assert_called()

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard_instance = mock_dashboard_cls.return_value
        mock_dashboard_instance.export_dashboard.return_value = True

        mock_notifier_instance = mock_notifier_cls.return_value
        mock_notifier_instance.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.random_repo_path)
        
        with patch.object(dispatcher, "dispatch_health_and_notify", wraps=dispatcher.dispatch_health_and_notify) as mock_dispatch_method:
            result = dispatcher.dispatch()

            self.assertTrue(result)
            expected_report_path = os.path.join(self.random_repo_path, "report.json")
            mock_dispatch_method.assert_called_once_with(expected_report_path)


if __name__ == "__main__":
    unittest.main()