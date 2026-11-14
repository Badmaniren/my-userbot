import unittest
from unittest.mock import patch, MagicMock
import io
import os
import uuid
import random
from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")
        self.title = uuid.uuid4().hex
        self.value = random.randint(1, 1000)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_notify_with_retry_success_on_first_try(self, mock_dashboard_cls, mock_notifier_cls):
        mock_notifier = mock_notifier_cls.return_value
        mock_notifier.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.repo_path)
        func = mock_notifier.notify
        result = dispatcher._notify_with_retry(func, self.file_path)

        self.assertTrue(result)
        mock_notifier.notify.assert_called_once_with(self.file_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_notify_with_retry_success_after_retries(self, mock_dashboard_cls, mock_notifier_cls):
        mock_notifier = mock_notifier_cls.return_value
        mock_notifier.notify.side_effect = [False, False, True]

        dispatcher = RepoHealthDispatcher(self.repo_path)
        func = mock_notifier.notify
        result = dispatcher._notify_with_retry(func, self.file_path)

        self.assertTrue(result)
        self.assertEqual(mock_notifier.notify.call_count, 3)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_notify_with_retry_all_fails(self, mock_dashboard_cls, mock_notifier_cls):
        mock_notifier = mock_notifier_cls.return_value
        mock_notifier.notify.return_value = False

        dispatcher = RepoHealthDispatcher(self.repo_path)
        func = mock_notifier.notify
        result = dispatcher._notify_with_retry(func, self.file_path)

        self.assertFalse(result)
        self.assertEqual(mock_notifier.notify.call_count, 3)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch_health_and_notify_success(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_dashboard.export_dashboard.return_value = True

        mock_notifier = mock_notifier_cls.return_value
        mock_notifier.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.dispatch_health_and_notify(self.file_path)

        self.assertTrue(result)
        mock_dashboard.generate_dashboard.assert_called_once()
        mock_dashboard.export_dashboard.assert_called_once_with(self.file_path)
        mock_notifier.notify.assert_called_once_with(self.file_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch_health_and_notify_export_fail(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_dashboard.export_dashboard.return_value = False

        mock_notifier = mock_notifier_cls.return_value

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.dispatch_health_and_notify(self.file_path)

        self.assertFalse(result)
        mock_dashboard.generate_dashboard.assert_called_once()
        mock_dashboard.export_dashboard.assert_called_once_with(self.file_path)
        mock_notifier.notify.assert_not_called()

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_process_stream_and_dispatch_with_string_stream(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_dashboard.export_dashboard.return_value = True

        mock_notifier = mock_notifier_cls.return_value
        mock_notifier.notify.return_value = True

        stream_data = uuid.uuid4().hex
        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.process_stream_and_dispatch(stream_data, self.file_path)

        self.assertTrue(result)
        mock_dashboard.process_stream.assert_called_once()
        mock_dashboard.export_dashboard.assert_called_once_with(self.file_path)
        mock_notifier.notify.assert_called_once_with(self.file_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_process_stream_and_dispatch_with_bytes_stream(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_dashboard.export_dashboard.return_value = True

        mock_notifier = mock_notifier_cls.return_value
        mock_notifier.notify.return_value = True

        stream_data = io.BytesIO(uuid.uuid4().hex.encode("utf-8"))
        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.process_stream_and_dispatch(stream_data, self.file_path)

        self.assertTrue(result)
        mock_dashboard.process_stream.assert_called_once_with(stream_data)
        mock_dashboard.export_dashboard.assert_called_once_with(self.file_path)
        mock_notifier.notify.assert_called_once_with(self.file_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_process_stream_and_dispatch_export_fail(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_dashboard.export_dashboard.return_value = False

        mock_notifier = mock_notifier_cls.return_value

        stream_data = uuid.uuid4().hex
        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.process_stream_and_dispatch(stream_data, self.file_path)

        self.assertFalse(result)
        mock_dashboard.process_stream.assert_called_once()
        mock_dashboard.export_dashboard.assert_called_once_with(self.file_path)
        mock_notifier.notify.assert_not_called()

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("builtins.open", new_callable=MagicMock)
    def test_check_and_notify_critical(self, mock_open, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        rendered_widget = uuid.uuid4().hex
        mock_dashboard.render_widget.return_value = rendered_widget

        mock_notifier = mock_notifier_cls.return_value
        mock_notifier.notify_and_commit.return_value = True

        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.check_and_notify_critical(self.title, self.value, self.file_path)

        self.assertTrue(result)
        mock_dashboard.render_widget.assert_called_once_with(self.title, self.value)
        mock_open.assert_called_once_with(self.file_path, "w", encoding="utf-8")
        mock_file.write.assert_called_once_with(rendered_widget)
        mock_notifier.notify_and_commit.assert_called()

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch_calls_dispatch_health_and_notify(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_dashboard.export_dashboard.return_value = True

        mock_notifier = mock_notifier_cls.return_value
        mock_notifier.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.repo_path)
        expected_report_path = os.path.join(self.repo_path, "report.json")

        result = dispatcher.dispatch()

        self.assertTrue(result)
        mock_dashboard.generate_dashboard.assert_called_once()
        mock_dashboard.export_dashboard.assert_called_once_with(expected_report_path)
        mock_notifier.notify.assert_called_once_with(expected_report_path)


if __name__ == "__main__":
    unittest.main()