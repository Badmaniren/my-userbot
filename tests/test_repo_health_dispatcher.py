import unittest
from unittest.mock import patch, mock_open
import os
import uuid
import random
import io
from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_dispatch_health_and_notify_success(self, mock_notifier_class, mock_dashboard_class):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        mock_dashboard_instance = mock_dashboard_class.return_value
        mock_dashboard_instance.export_dashboard.return_value = True

        mock_notifier_instance = mock_notifier_class.return_value
        mock_notifier_instance.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.dispatch_health_and_notify(file_path)

        self.assertTrue(result)
        mock_dashboard_instance.generate_dashboard.assert_called_once()
        mock_dashboard_instance.export_dashboard.assert_called_once_with(file_path)
        mock_notifier_instance.notify.assert_called_once_with(file_path)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_dispatch_health_and_notify_export_fail(self, mock_notifier_class, mock_dashboard_class):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        mock_dashboard_instance = mock_dashboard_class.return_value
        mock_dashboard_instance.export_dashboard.return_value = False

        mock_notifier_instance = mock_notifier_class.return_value

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.dispatch_health_and_notify(file_path)

        self.assertFalse(result)
        mock_dashboard_instance.generate_dashboard.assert_called_once()
        mock_dashboard_instance.export_dashboard.assert_called_once_with(file_path)
        mock_notifier_instance.notify.assert_not_called()

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_process_stream_and_dispatch_with_string_stream(self, mock_notifier_class, mock_dashboard_class):
        stream_content = uuid.uuid4().hex
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"

        mock_dashboard_instance = mock_dashboard_class.return_value
        mock_notifier_instance = mock_notifier_class.return_value
        mock_notifier_instance.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.process_stream_and_dispatch(stream_content, file_path)

        self.assertTrue(result)
        mock_dashboard_instance.process_stream.assert_called_once()
        mock_dashboard_instance.export_dashboard.assert_called_once_with(file_path)
        mock_notifier_instance.notify.assert_called_once_with(file_path)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_process_stream_and_dispatch_with_bytesio_stream(self, mock_notifier_class, mock_dashboard_class):
        stream_bytes = io.BytesIO(uuid.uuid4().hex.encode("utf-8"))
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"

        mock_dashboard_instance = mock_dashboard_class.return_value
        mock_notifier_instance = mock_notifier_class.return_value
        mock_notifier_instance.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.process_stream_and_dispatch(stream_bytes, file_path)

        self.assertTrue(result)
        mock_dashboard_instance.process_stream.assert_called_once_with(stream_bytes)
        mock_dashboard_instance.export_dashboard.assert_called_once_with(file_path)
        mock_notifier_instance.notify.assert_called_once_with(file_path)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_check_and_notify_critical(self, mock_notifier_class, mock_dashboard_class):
        title = uuid.uuid4().hex
        value = random.randint(1, 100)
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt"
        rendered_widget = uuid.uuid4().hex

        mock_dashboard_instance = mock_dashboard_class.return_value
        mock_dashboard_instance.render_widget.return_value = rendered_widget

        mock_notifier_instance = mock_notifier_class.return_value
        mock_notifier_instance.notify_and_commit.return_value = True

        m_open = mock_open()
        with patch("builtins.open", m_open):
            dispatcher = RepoHealthDispatcher(self.repo_path)
            result = dispatcher.check_and_notify_critical(title, value, file_path)

        self.assertTrue(result)
        mock_dashboard_instance.render_widget.assert_called_once_with(title, value)
        m_open.assert_called_once_with(file_path, "w", encoding="utf-8")
        m_open().write.assert_called_once_with(rendered_widget)
        mock_notifier_instance.notify_and_commit.assert_called_once()

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_notify_with_retry_eventual_success(self, mock_notifier_class, mock_dashboard_class):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        mock_dashboard_instance = mock_dashboard_class.return_value
        mock_dashboard_instance.export_dashboard.return_value = True

        mock_notifier_instance = mock_notifier_class.return_value
        mock_notifier_instance.notify.side_effect = [False, False, True]

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.dispatch_health_and_notify(file_path)

        self.assertTrue(result)
        self.assertEqual(mock_notifier_instance.notify.call_count, 3)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_notify_with_retry_complete_failure(self, mock_notifier_class, mock_dashboard_class):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        mock_dashboard_instance = mock_dashboard_class.return_value
        mock_dashboard_instance.export_dashboard.return_value = True

        mock_notifier_instance = mock_notifier_class.return_value
        mock_notifier_instance.notify.return_value = False

        dispatcher = RepoHealthDispatcher(self.repo_path)
        result = dispatcher.dispatch_health_and_notify(file_path)

        self.assertFalse(result)
        self.assertEqual(mock_notifier_instance.notify.call_count, 3)

    @patch("skills.repo_health_dispatcher.RepoHealthDashboard")
    @patch("skills.repo_health_dispatcher.RepoNotifier")
    def test_dispatch_delegation(self, mock_notifier_class, mock_dashboard_class):
        mock_dashboard_instance = mock_dashboard_class.return_value
        mock_dashboard_instance.export_dashboard.return_value = True
        mock_notifier_instance = mock_notifier_class.return_value
        mock_notifier_instance.notify.return_value = True

        dispatcher = RepoHealthDispatcher(self.repo_path)
        
        with patch.object(dispatcher, "dispatch_health_and_notify", return_value=True) as mock_dispatch_health:
            result = dispatcher.dispatch()
            self.assertTrue(result)
            mock_dispatch_health.assert_called_once_with(os.path.join(self.repo_path, "report.json"))