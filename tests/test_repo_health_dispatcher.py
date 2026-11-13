import io
import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, mock_open, patch

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def test_init(self):
        repo_path = f"path_{uuid.uuid4().hex}"
        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dash_cls, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notifier_cls:
            dispatcher = RepoHealthDispatcher(repo_path)
            self.assertEqual(dispatcher.repo_path, repo_path)
            mock_dash_cls.assert_called_once_with(repo_path)
            mock_notifier_cls.assert_called_once_with(repo_path)

    def test_dispatch_health_and_notify_success(self):
        repo_path = f"repo_{uuid.uuid4().hex}"
        file_path = f"report_{uuid.uuid4().hex}.json"
        notify_result = random.choice([True, False])

        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dash_cls, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notifier_cls:

            mock_dash_inst = MagicMock()
            mock_dash_cls.return_value = mock_dash_inst
            mock_dash_inst.export_dashboard.return_value = True

            mock_notifier_inst = MagicMock()
            mock_notifier_cls.return_value = mock_notifier_inst
            mock_notifier_inst.notify.return_value = notify_result

            dispatcher = RepoHealthDispatcher(repo_path)
            result = dispatcher.dispatch_health_and_notify(file_path)

            mock_dash_inst.generate_dashboard.assert_called_once()
            mock_dash_inst.export_dashboard.assert_called_once_with(file_path)
            mock_notifier_inst.notify.assert_called_once_with(file_path)
            self.assertEqual(result, notify_result)

    def test_dispatch_health_and_notify_export_failed(self):
        repo_path = f"repo_{uuid.uuid4().hex}"
        file_path = f"report_{uuid.uuid4().hex}.json"

        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dash_cls, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notifier_cls:

            mock_dash_inst = MagicMock()
            mock_dash_cls.return_value = mock_dash_inst
            mock_dash_inst.export_dashboard.return_value = False

            mock_notifier_inst = MagicMock()
            mock_notifier_cls.return_value = mock_notifier_inst

            dispatcher = RepoHealthDispatcher(repo_path)
            result = dispatcher.dispatch_health_and_notify(file_path)

            mock_dash_inst.generate_dashboard.assert_called_once()
            mock_dash_inst.export_dashboard.assert_called_once_with(file_path)
            mock_notifier_inst.notify.assert_not_called()
            self.assertFalse(result)

    def test_process_stream_and_dispatch_string_stream(self):
        repo_path = f"repo_{uuid.uuid4().hex}"
        file_path = f"out_{uuid.uuid4().hex}.json"
        raw_stream_str = f"stream_payload_{uuid.uuid4().hex}"
        expected_bytes = raw_stream_str.encode("utf-8")
        notify_result = random.choice([True, False])

        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dash_cls, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notifier_cls:

            mock_dash_inst = MagicMock()
            mock_dash_cls.return_value = mock_dash_inst
            mock_notifier_inst = MagicMock()
            mock_notifier_cls.return_value = mock_notifier_inst
            mock_notifier_inst.notify.return_value = notify_result

            dispatcher = RepoHealthDispatcher(repo_path)
            result = dispatcher.process_stream_and_dispatch(raw_stream_str, file_path)

            self.assertTrue(mock_dash_inst.process_stream.called)
            passed_stream = mock_dash_inst.process_stream.call_args[0][0]
            self.assertIsInstance(passed_stream, io.BytesIO)
            self.assertEqual(passed_stream.getvalue(), expected_bytes)

            mock_dash_inst.export_dashboard.assert_called_once_with(file_path)
            mock_notifier_inst.notify.assert_called_once_with(file_path)
            self.assertEqual(result, notify_result)

    def test_process_stream_and_dispatch_bytes_stream(self):
        repo_path = f"repo_{uuid.uuid4().hex}"
        file_path = f"out_{uuid.uuid4().hex}.json"
        random_payload = uuid.uuid4().bytes + bytes([random.randint(0, 255) for _ in range(8)])
        stream_obj = io.BytesIO(random_payload)
        notify_result = random.choice([True, False])

        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dash_cls, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notifier_cls:

            mock_dash_inst = MagicMock()
            mock_dash_cls.return_value = mock_dash_inst
            mock_notifier_inst = MagicMock()
            mock_notifier_cls.return_value = mock_notifier_inst
            mock_notifier_inst.notify.return_value = notify_result

            dispatcher = RepoHealthDispatcher(repo_path)
            result = dispatcher.process_stream_and_dispatch(stream_obj, file_path)

            mock_dash_inst.process_stream.assert_called_once_with(stream_obj)
            mock_dash_inst.export_dashboard.assert_called_once_with(file_path)
            mock_notifier_inst.notify.assert_called_once_with(file_path)
            self.assertEqual(result, notify_result)

    def test_check_and_notify_critical(self):
        repo_path = f"repo_{uuid.uuid4().hex}"
        file_path = f"critical_{uuid.uuid4().hex}.widget"
        title = f"Title_{uuid.uuid4().hex}"
        value = random.randint(100, 999999)
        rendered_content = f"WidgetData_{uuid.uuid4().hex}"
        notify_commit_result = random.choice([True, False])

        m_open = mock_open()

        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dash_cls, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notifier_cls, \
             patch("builtins.open", m_open):

            mock_dash_inst = MagicMock()
            mock_dash_cls.return_value = mock_dash_inst
            mock_dash_inst.render_widget.return_value = rendered_content

            mock_notifier_inst = MagicMock()
            mock_notifier_cls.return_value = mock_notifier_inst
            mock_notifier_inst.notify_and_commit.return_value = notify_commit_result

            dispatcher = RepoHealthDispatcher(repo_path)
            result = dispatcher.check_and_notify_critical(title, value, file_path)

            mock_dash_inst.render_widget.assert_called_once_with(title, value)
            m_open.assert_called_once_with(file_path, "w", encoding="utf-8")
            m_open().write.assert