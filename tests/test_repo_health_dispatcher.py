import io
import os
import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, mock_open, patch

from skills.repo_health_dispatcher import RepoHealthDispatcher


def get_random_string(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def get_random_path():
    return os.path.join(
        "/",
        get_random_string(6),
        get_random_string(8),
        f"{get_random_string(10)}.json",
    )


class TestRepoHealthDispatcher(unittest.TestCase):

    def test_init(self):
        fake_repo_path = get_random_path()
        with (
            patch(
                "skills.repo_health_dispatcher.RepoHealthDashboard"
            ) as mock_dashboard_cls,
            patch(
                "skills.repo_health_dispatcher.RepoNotifier"
            ) as mock_notifier_cls,
        ):
            dispatcher = RepoHealthDispatcher(fake_repo_path)
            self.assertEqual(dispatcher.repo_path, fake_repo_path)
            mock_dashboard_cls.assert_called_once_with(fake_repo_path)
            mock_notifier_cls.assert_called_once_with(fake_repo_path)

    def test_dispatch_health_and_notify_success(self):
        fake_repo_path = get_random_path()
        target_file_path = get_random_path()
        expected_notify_result = random.choice([True, False])

        with (
            patch(
                "skills.repo_health_dispatcher.RepoHealthDashboard"
            ) as mock_dash_cls,
            patch(
                "skills.repo_health_dispatcher.RepoNotifier"
            ) as mock_notif_cls,
        ):
            mock_dash = mock_dash_cls.return_value
            mock_notif = mock_notif_cls.return_value

            mock_dash.export_dashboard.return_value = True
            mock_notif.notify.return_value = expected_notify_result

            dispatcher = RepoHealthDispatcher(fake_repo_path)
            result = dispatcher.dispatch_health_and_notify(target_file_path)

            mock_dash.generate_dashboard.assert_called_once()
            mock_dash.export_dashboard.assert_called_once_with(target_file_path)
            mock_notif.notify.assert_called_once_with(target_file_path)
            self.assertEqual(result, expected_notify_result)

    def test_dispatch_health_and_notify_export_failure(self):
        fake_repo_path = get_random_path()
        target_file_path = get_random_path()

        with (
            patch(
                "skills.repo_health_dispatcher.RepoHealthDashboard"
            ) as mock_dash_cls,
            patch(
                "skills.repo_health_dispatcher.RepoNotifier"
            ) as mock_notif_cls,
        ):
            mock_dash = mock_dash_cls.return_value
            mock_notif = mock_notif_cls.return_value

            mock_dash.export_dashboard.return_value = False

            dispatcher = RepoHealthDispatcher(fake_repo_path)
            result = dispatcher.dispatch_health_and_notify(target_file_path)

            mock_dash.generate_dashboard.assert_called_once()
            mock_dash.export_dashboard.assert_called_once_with(target_file_path)
            mock_notif.notify.assert_not_called()
            self.assertFalse(result)

    def test_process_stream_and_dispatch_with_string_stream(self):
        fake_repo_path = get_random_path()
        target_file_path = get_random_path()
        raw_text_stream = f"stream_data_{uuid.uuid4().hex}"
        expected_notify_result = random.choice([True, False])

        with (
            patch(
                "skills.repo_health_dispatcher.RepoHealthDashboard"
            ) as mock_dash_cls,
            patch(
                "skills.repo_health_dispatcher.RepoNotifier"
            ) as mock_notif_cls,
        ):
            mock_dash = mock_dash_cls.return_value
            mock_notif = mock_notif_cls.return_value
            mock_notif.notify.return_value = expected_notify_result

            dispatcher = RepoHealthDispatcher(fake_repo_path)
            result = dispatcher.process_stream_and_dispatch(
                raw_text_stream, target_file_path
            )

            mock_dash.process_stream.assert_called_once()
            passed_stream = mock_dash.process_stream.call_args[0][0]
            self.assertIsInstance(passed_stream, io.BytesIO)
            self.assertEqual(
                passed_stream.getvalue(), raw_text_stream.encode("utf-8")
            )

            mock_dash.export_dashboard.assert_called_once_with(target_file_path)
            mock_notif.notify.assert_called_once_with(target_file_path)
            self.assertEqual(result, expected_notify_result)

    def test_process_stream_and_dispatch_with_bytes_stream(self):
        fake_repo_path = get_random_path()
        target_file_path = get_random_path()
        random_bytes = uuid.uuid4().hex.encode("utf-8")
        byte_stream = io.BytesIO(random_bytes)
        expected_notify_result = random.choice([True, False])

        with (
            patch(
                "skills.repo_health_dispatcher.RepoHealthDashboard"
            ) as mock_dash_cls,
            patch(
                "skills.repo_health_dispatcher.RepoNotifier"
            ) as mock_notif_cls,
        ):
            mock_dash = mock_dash_cls.return_value
            mock_notif = mock_notif_cls.return_value
            mock_notif.notify.return_value = expected_notify_result

            dispatcher = RepoHealthDispatcher(fake_repo_path)
            result = dispatcher.process_stream_and_dispatch(
                byte_stream, target_file_path
            )

            mock_dash.process_stream.assert_called_once_with(byte_stream)
            mock_dash.export_dashboard.assert_called_once_with(target_file_path)
            mock_notif.notify.assert_called_once_with(target_file_path)
            self.assertEqual(result, expected_notify_result)

    def test_check_and_notify_critical(self):
        fake_repo_path = get_random_path()
        target_file_path = get_random_path()
        random_title = f"Title_{uuid.uuid4().hex}"
        random_value = random.randint(1000, 9999)
        rendered_widget_content = f"WidgetContent_{uuid.uuid4().hex}"
        expected_notify_result = random.choice([True, False])

        m_open = mock_open()
        with (
            patch(
                "skills.repo_health_dispatcher.RepoHealthDashboard"
            ) as mock_dash_cls,
            patch(
                "skills.repo_health_dispatcher.RepoNotifier"
            ) as mock_notif_cls,
            patch("builtins.open", m_open),
        ):
            mock_dash = mock_dash_cls.return_value
            mock_notif = mock_notif_cls.return_value

            mock_dash.render_widget.return_value = rendered_widget_content
            mock_notif.notify_and_commit.return_value = expected_notify_result

            dispatcher = RepoHealthDispatcher(fake_repo_path)
            result = dispatcher.check_and_notify_critical(
                random_title, random_value, target_file_path
            )

            mock_dash.render_widget.assert_called_once_with(
                random_title, random_value
            )
            m_open.assert_called_once_with(target_file_path, "w", encoding="utf-8")
            handle = m_open()
            handle.write.assert_called_once_with(rendered_widget_content)
            mock_notif.notify_and_commit.assert_called_once()
            self.assertEqual(result, expected_notify_result)

    def test_dispatch(self):
        fake_repo_path = get_random_path()
        expected_report_path = os.path.join(fake_repo_path, "report.json")
        expected_dispatch_result = random.choice([True, False])

        with (
            patch("skills.repo_health_dispatcher.RepoHealthDashboard"),
            patch("skills.repo_health_dispatcher.RepoNotifier"),
        ):
            dispatcher = RepoHealthDispatcher(fake_repo_path)
            with patch.object(
                dispatcher,
                "dispatch_health_and_notify",
                return_value=expected_dispatch_result,
            ) as mock_dispatch_health:
                result = dispatcher.dispatch()
                mock_dispatch_health.assert_called_once_with(expected_report_path)
                self.assertEqual(result, expected_dispatch_result)


if __name__ == "__main__":
    unittest.main()