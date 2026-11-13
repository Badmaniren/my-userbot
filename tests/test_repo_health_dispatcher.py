import io
import os
import random
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = os.path.join(
            "/tmp", f"repo_{uuid.uuid4().hex[:8]}"
        )

    def test_dispatch_health_and_notify_success(self):
        random_file_path = os.path.join(
            self.repo_path, f"{uuid.uuid4().hex}.json"
        )

        with patch(
            "skills.repo_health_dispatcher.RepoHealthDashboard"
        ) as mock_dashboard_cls, patch(
            "skills.repo_health_dispatcher.RepoNotifier"
        ) as mock_notifier_cls:

            mock_dashboard_instance = mock_dashboard_cls.return_value
            mock_dashboard_instance.export_dashboard.return_value = True

            mock_notifier_instance = mock_notifier_cls.return_value
            expected_notify_result = random.choice([True, False])
            mock_notifier_instance.notify.return_value = (
                expected_notify_result
            )

            dispatcher = RepoHealthDispatcher(self.repo_path)
            result = dispatcher.dispatch_health_and_notify(random_file_path)

            mock_dashboard_instance.generate_dashboard.assert_called_once()
            mock_dashboard_instance.export_dashboard.assert_called_once_with(
                random_file_path
            )
            mock_notifier_instance.notify.assert_called_once_with(
                random_file_path
            )
            self.assertEqual(result, expected_notify_result)

    def test_dispatch_health_and_notify_export_failure(self):
        random_file_path = os.path.join(
            self.repo_path, f"{uuid.uuid4().hex}.json"
        )

        with patch(
            "skills.repo_health_dispatcher.RepoHealthDashboard"
        ) as mock_dashboard_cls, patch(
            "skills.repo_health_dispatcher.RepoNotifier"
        ) as mock_notifier_cls:

            mock_dashboard_instance = mock_dashboard_cls.return_value
            mock_dashboard_instance.export_dashboard.return_value = False

            mock_notifier_instance = mock_notifier_cls.return_value

            dispatcher = RepoHealthDispatcher(self.repo_path)
            result = dispatcher.dispatch_health_and_notify(random_file_path)

            mock_dashboard_instance.generate_dashboard.assert_called_once()
            mock_dashboard_instance.export_dashboard.assert_called_once_with(
                random_file_path
            )
            mock_notifier_instance.notify.assert_not_called()
            self.assertFalse(result)

    def test_process_stream_and_dispatch_with_string(self):
        random_stream_content = uuid.uuid4().hex
        random_file_path = os.path.join(
            self.repo_path, f"{uuid.uuid4().hex}.report"
        )

        with patch(
            "skills.repo_health_dispatcher.RepoHealthDashboard"
        ) as mock_dashboard_cls, patch(
            "skills.repo_health_dispatcher.RepoNotifier"
        ) as mock_notifier_cls:

            mock_dashboard_instance = mock_dashboard_cls.return_value
            mock_notifier_instance = mock_notifier_cls.return_value
            expected_result = random.choice([True, False])
            mock_notifier_instance.notify.return_value = expected_result

            dispatcher = RepoHealthDispatcher(self.repo_path)
            result = dispatcher.process_stream_and_dispatch(
                random_stream_content, random_file_path
            )

            mock_dashboard_instance.process_stream.assert_called_once()
            call_arg = mock_dashboard_instance.process_stream.call_args[0][0]
            self.assertIsInstance(call_arg, io.BytesIO)
            self.assertEqual(
                call_arg.read(), random_stream_content.encode("utf-8")
            )

            mock_dashboard_instance.export_dashboard.assert_called_once_with(
                random_file_path
            )
            mock_notifier_instance.notify.assert_called_once_with(
                random_file_path
            )
            self.assertEqual(result, expected_result)

    def test_process_stream_and_dispatch_with_bytesio(self):
        random_bytes = uuid.uuid4().hex.encode("utf-8")
        stream = io.BytesIO(random_bytes)
        random_file_path = os.path.join(
            self.repo_path, f"{uuid.uuid4().hex}.report"
        )

        with patch(
            "skills.repo_health_dispatcher.RepoHealthDashboard"
        ) as mock_dashboard_cls, patch(
            "skills.repo_health_dispatcher.RepoNotifier"
        ) as mock_notifier_cls:

            mock_dashboard_instance = mock_dashboard_cls.return_value
            mock_notifier_instance = mock_notifier_cls.return_value
            expected_result = random.choice([True, False])
            mock_notifier_instance.notify.return_value = expected_result

            dispatcher = RepoHealthDispatcher(self.repo_path)
            result = dispatcher.process_stream_and_dispatch(
                stream, random_file_path
            )

            mock_dashboard_instance.process_stream.assert_called_once_with(
                stream
            )
            mock_dashboard_instance.export_dashboard.assert_called_once_with(
                random_file_path
            )
            mock_notifier_instance.notify.assert_called_once_with(
                random_file_path
            )
            self.assertEqual(result, expected_result)

    def test_check_and_notify_critical(self):
        random_title = f"Title_{uuid.uuid4().hex}"
        random_value = random.randint(1, 1000)
        random_file_path = os.path.join(
            self.repo_path, f"{uuid.uuid4().hex}.widget"
        )
        random_widget_str = f"<widget>{uuid.uuid4().hex}</widget>"

        with patch(
            "skills.repo_health_dispatcher.RepoHealthDashboard"
        ) as mock_dashboard_cls, patch(
            "skills.repo_health_dispatcher.RepoNotifier"
        ) as mock_notifier_cls, patch(
            "builtins.open", new_callable=unittest.mock.mock_open
        ) as mock_file:

            mock_dashboard_instance = mock_dashboard_cls.return_value
            mock_dashboard_instance.render_widget.return_value = (
                random_widget_str
            )

            mock_notifier_instance = mock_notifier_cls.return_value
            expected_result = random.choice([True, False])
            mock_notifier_instance.notify_and_commit.return_value = (
                expected_result
            )

            dispatcher = RepoHealthDispatcher(self.repo_path)
            result = dispatcher.check_and_notify_critical(
                random_title, random_value, random_file_path
            )

            mock_dashboard_instance.render_widget.assert_called_once_with(
                random_title, random_value
            )
            mock_file.assert_called_once_with(
                random_file_path, "w", encoding="utf-8"
            )
            mock_file().write.assert_called_once_with(random_widget_str)
            mock_notifier_instance.notify_and_commit.assert_called_once()
            self.assertEqual(result, expected_result)

    def test_dispatch(self):
        with patch(
            "skills.repo_health_dispatcher.RepoHealthDispatcher.dispatch_health_and_notify"
        ) as mock_dispatch_health:
            expected_result = random.choice([True, False])
            mock_dispatch_health.return_value = expected_result

            dispatcher = RepoHealthDispatcher(self.repo_path)
            result = dispatcher.dispatch()

            expected_path = os.path.join(self.repo_path, "report.json")
            mock_dispatch_health.assert_called_once_with(expected_path)
            self.assertEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()