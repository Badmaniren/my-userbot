import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def test_init(self):
        self.assertEqual(self.dispatcher.repo_path, self.repo_path)

    def test_dispatch_health_and_notify_success(self):
        rand_status = random.choice([uuid.uuid4().hex, uuid.uuid4().hex])
        rand_metric = random.randint(100, 999)
        dashboard_data = {
            "status": rand_status,
            "metric": rand_metric,
            "issues_count": 0
        }

        rand_file_path = f"/tmp/report_{uuid.uuid4().hex}.json"

        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dashboard_cls, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notifier_cls:
            
            mock_dashboard_instance = mock_dashboard_cls.return_value
            mock_dashboard_instance.generate_dashboard.return_value = dashboard_data
            mock_dashboard_instance.export_dashboard.return_value = True

            mock_notifier_instance = mock_notifier_cls.return_value
            mock_notifier_instance.notify.return_value = True

            result = self.dispatcher.dispatch_health_and_notify(rand_file_path)

            mock_dashboard_cls.assert_called_once_with(self.repo_path)
            mock_dashboard_instance.generate_dashboard.assert_called_once()
            mock_dashboard_instance.export_dashboard.assert_called_once_with(rand_file_path)

            mock_notifier_cls.assert_called_once_with(self.repo_path)
            mock_notifier_instance.notify.assert_called_once_with(rand_file_path)

            self.assertTrue(result)

    def test_dispatch_health_and_notify_export_failure(self):
        rand_file_path = f"/tmp/report_{uuid.uuid4().hex}.json"
        dashboard_data = {"status": uuid.uuid4().hex}

        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dashboard_cls, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notifier_cls:
            
            mock_dashboard_instance = mock_dashboard_cls.return_value
            mock_dashboard_instance.generate_dashboard.return_value = dashboard_data
            mock_dashboard_instance.export_dashboard.return_value = False

            mock_notifier_instance = mock_notifier_cls.return_value

            result = self.dispatcher.dispatch_health_and_notify(rand_file_path)

            mock_dashboard_instance.export_dashboard.assert_called_once_with(rand_file_path)
            mock_notifier_instance.notify.assert_not_called()

            self.assertFalse(result)

    def test_process_stream_and_dispatch(self):
        rand_stream_data = "".join(random.choices(string.ascii_letters + string.digits, k=50))
        stream = io.BytesIO(rand_stream_data.encode('utf-8'))
        rand_file_path = f"/tmp/report_{uuid.uuid4().hex}.json"
        dashboard_result = {"processed_id": uuid.uuid4().hex}

        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dashboard_cls, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notifier_cls:
            
            mock_dashboard_instance = mock_dashboard_cls.return_value
            mock_dashboard_instance.process_stream.return_value = dashboard_result
            mock_dashboard_instance.export_dashboard.return_value = True

            mock_notifier_instance = mock_notifier_cls.return_value
            mock_notifier_instance.notify.return_value = True

            result = self.dispatcher.process_stream_and_dispatch(stream, rand_file_path)

            mock_dashboard_instance.process_stream.assert_called_once_with(stream)
            mock_dashboard_instance.export_dashboard.assert_called_once_with(rand_file_path)
            mock_notifier_instance.notify.assert_called_once_with(rand_file_path)

            self.assertTrue(result)

    def test_check_and_notify_critical(self):
        rand_title = uuid.uuid4().hex
        rand_val = random.randint(1, 100)
        widget_str = f"Widget: {rand_title}={rand_val}"
        rand_file_path = f"/tmp/crit_{uuid.uuid4().hex}.log"

        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dashboard_cls, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notifier_cls:
            
            mock_dashboard_instance = mock_dashboard_cls.return_value
            mock_dashboard_instance.render_widget.return_value = widget_str

            mock_notifier_instance = mock_notifier_cls.return_value
            mock_notifier_instance.notify_and_commit.return_value = True

            with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
                result = self.dispatcher.check_and_notify_critical(rand_title, rand_val, rand_file_path)

                mock_dashboard_instance.render_widget.assert_called_once_with(rand_title, rand_val)
                mock_file.assert_called_once_with(rand_file_path, "w", encoding="utf-8")
                mock_file().write.assert_called_once_with(widget_str)
                mock_notifier_instance.notify_and_commit.assert_called_once()
                self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()