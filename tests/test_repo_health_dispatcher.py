import io
import os
import random
import unittest
from unittest.mock import MagicMock, patch, mock_open
import uuid
string = __import__('string')

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = os.path.join(
            "/tmp", f"repo_{uuid.uuid4().hex[:8]}"
        )
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch_health_and_notify_success(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_notifier = mock_notifier_cls.return_value

        mock_dashboard.export_dashboard.return_value = True
        mock_notifier.notify.return_value = True

        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")
        
        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.dispatch_health_and_notify(file_path)

        self.assertTrue(result)
        mock_dashboard.generate_dashboard.assert_called_once()
        mock_dashboard.export_dashboard.assert_called_once_with(file_path)
        mock_notifier.notify.assert_called_once_with(file_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch_health_and_notify_export_failure(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_notifier = mock_notifier_cls.return_value

        mock_dashboard.export_dashboard.return_value = False

        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.dispatch_health_and_notify(file_path)

        self.assertFalse(result)
        mock_dashboard.generate_dashboard.assert_called_once()
        mock_dashboard.export_dashboard.assert_called_once_with(file_path)
        mock_notifier.notify.assert_not_called()

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_process_stream_and_dispatch_with_string_stream(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_notifier = mock_notifier_cls.return_value
        mock_notifier.notify.return_value = True

        random_stream_data = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.yaml")

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.process_stream_and_dispatch(random_stream_data, file_path)

        self.assertTrue(result)
        mock_dashboard.process_stream.assert_called_once()
        args, _ = mock_dashboard.process_stream.call_args
        self.assertIsInstance(args[0], io.BytesIO)
        self.assertEqual(args[0].read().decode("utf-8"), random_stream_data)
        mock_dashboard.export_dashboard.assert_called_once_with(file_path)
        mock_notifier.notify.assert_called_once_with(file_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_process_stream_and_dispatch_with_bytes_stream(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_notifier = mock_notifier_cls.return_value
        mock_notifier.notify.return_value = False

        random_bytes = uuid.uuid4().bytes
        stream_obj = io.BytesIO(random_bytes)
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.xml")

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.process_stream_and_dispatch(stream_obj, file_path)

        self.assertFalse(result)
        mock_dashboard.process_stream.assert_called_once_with(stream_obj)
        mock_dashboard.export_dashboard.assert_called_once_with(file_path)
        mock_notifier.notify.assert_called_once_with(file_path)

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_check_and_notify_critical(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_notifier = mock_notifier_cls.return_value
        mock_notifier.notify_and_commit.return_value = True

        random_title = f"Crit_{uuid.uuid4().hex[:6]}"
        random_value = random.randint(100, 999)
        rendered_widget_content = f"WIDGET::{uuid.uuid4().hex}"
        mock_dashboard.render_widget.return_value = rendered_widget_content

        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.log")

        with patch("builtins.open", mock_open()) as mock_file:
            dispatcher = RepoHealthDispatcher(self.repo_path)
            result = dispatcher.check_and_notify_critical(random_title, random_value, file_path)

            self.assertTrue(result)
            mock_dashboard.render_widget.assert_called_once_with(random_title, random_value)
            mock_file.assert_called_once_with(file_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(rendered_widget_content)
            mock_notifier.notify_and_commit.assert_called_once()

    @patch("skills.repo_health_dispatcher.RepoNotifier")
    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    def test_dispatch_delegation(self, mock_dashboard_cls, mock_notifier_cls):
        mock_dashboard = mock_dashboard_cls.return_value
        mock_notifier = mock_notifier_cls.return_value
        mock_dashboard.export_dashboard.return_value = True
        mock_notifier.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.repo_path)
        
        with patch.object(dispatcher, 'dispatch_health_and_notify', wraps=dispatcher.dispatch_health_and_notify) as mock_dispatch_hn:
            result = dispatcher.dispatch()
            
            self.assertTrue(result)
            expected_report_path = os.path.join(self.repo_path, "report.json")
            mock_dispatch_hn.assert_called_once_with(expected_report_path)


if __name__ == "__main__":
    unittest.main()