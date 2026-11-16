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
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_notify_with_retry_success(self, mock_notifier_class, mock_dashboard_class):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        mock_notify_func = MagicMock(return_value=True)
        
        result = dispatcher._notify_with_retry(mock_notify_func)
        
        self.assertTrue(result)
        mock_notify_func.assert_called_once()

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_notify_with_retry_eventual_success(self, mock_notifier_class, mock_dashboard_class):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        mock_notify_func = MagicMock(side_effect=[Exception("fail"), True])
        
        result = dispatcher._notify_with_retry(mock_notify_func)
        
        self.assertTrue(result)
        self.assertEqual(mock_notify_func.call_count, 2)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_notify_with_retry_exhausted(self, mock_notifier_class, mock_dashboard_class):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        mock_notify_func = MagicMock(side_effect=Exception("persistent fail"))
        
        result = dispatcher._notify_with_retry(mock_notify_func)
        
        self.assertFalse(result)
        self.assertEqual(mock_notify_func.call_count, 3)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_dispatch_health_and_notify_success(self, mock_notifier_class, mock_dashboard_class):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        dispatcher = RepoHealthDispatcher(self.repo_path)
        dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=True)
        dispatcher.repo_notifier.notify = MagicMock(return_value=True)

        result = dispatcher.dispatch_health_and_notify(file_path)

        self.assertTrue(result)
        dispatcher.repo_health_dashboard.generate_dashboard.assert_called_once()
        dispatcher.repo_health_dashboard.export_dashboard.assert_called_once_with(file_path)
        dispatcher.repo_notifier.notify.assert_called_once_with(file_path)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_dispatch_health_and_notify_export_fail(self, mock_notifier_class, mock_dashboard_class):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        dispatcher = RepoHealthDispatcher(self.repo_path)
        dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=False)

        result = dispatcher.dispatch_health_and_notify(file_path)

        self.assertFalse(result)
        dispatcher.repo_health_dashboard.generate_dashboard.assert_called_once()
        dispatcher.repo_health_dashboard.export_dashboard.assert_called_once_with(file_path)
        dispatcher.repo_notifier.notify.assert_not_called()

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_process_stream_and_dispatch_with_string(self, mock_notifier_class, mock_dashboard_class):
        stream_data = uuid.uuid4().hex
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"

        dispatcher = RepoHealthDispatcher(self.repo_path)
        dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=True)
        dispatcher.repo_notifier.notify = MagicMock(return_value=True)

        result = dispatcher.process_stream_and_dispatch(stream_data, file_path)

        self.assertTrue(result)
        dispatcher.repo_health_dashboard.process_stream.assert_called_once()
        dispatcher.repo_health_dashboard.export_dashboard.assert_called_once_with(file_path)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_process_stream_and_dispatch_with_bytesio(self, mock_notifier_class, mock_dashboard_class):
        stream_data = io.BytesIO(uuid.uuid4().hex.encode("utf-8"))
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"

        dispatcher = RepoHealthDispatcher(self.repo_path)
        dispatcher.repo_health_dashboard.export_dashboard = MagicMock(return_value=True)
        dispatcher.repo_notifier.notify = MagicMock(return_value=True)

        result = dispatcher.process_stream_and_dispatch(stream_data, file_path)

        self.assertTrue(result)
        dispatcher.repo_health_dashboard.process_stream.assert_called_once_with(stream_data)

    @patch("skills.repo_health_dispatcher.open")
    @patch("skills.repo_health_dispatcher.os.makedirs")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_check_and_notify_critical(self, mock_notifier_class, mock_dashboard_class, mock_makedirs, mock_open):
        title = uuid.uuid4().hex
        value = random.randint(100, 999)
        file_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        widget_content = f"widget-{uuid.uuid4().hex}"

        dispatcher = RepoHealthDispatcher(self.repo_path)
        dispatcher.repo_health_dashboard.render_widget = MagicMock(return_value=widget_content)
        dispatcher.repo_notifier.notify_and_commit = MagicMock(return_value=True)

        mock_file_instance = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file_instance

        result = dispatcher.check_and_notify_critical(title, value, file_path)

        self.assertTrue(result)
        dispatcher.repo_health_dashboard.render_widget.assert_called_once_with(title, value)
        mock_makedirs.assert_called_once()
        mock_open.assert_called_once_with(file_path, "w", encoding="utf-8")
        mock_file_instance.write.assert_called_once_with(widget_content)
        dispatcher.repo_notifier.notify_and_commit.assert_called_once_with(file_path)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_dispatch(self, mock_notifier_class, mock_dashboard_class):
        dispatcher = RepoHealthDispatcher(self.repo_path)
        expected_report_path = os.path.join(self.repo_path, "report.json")
        
        dispatcher.dispatch_health_and_notify = MagicMock(return_value=True)

        result = dispatcher.dispatch()

        self.assertTrue(result)
        dispatcher.dispatch_health_and_notify.assert_called_once_with(expected_report_path)


if __name__ == "__main__":
    unittest.main()