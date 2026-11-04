import unittest
from unittest.mock import patch
import tempfile
import shutil
import os
import uuid
import random
import io
from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.dispatcher = RepoHealthDispatcher(self.repo_path)
        self.random_file_name = f"{uuid.uuid4().hex}.json"
        self.file_path = os.path.join(self.test_dir, self.random_file_name)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_sets_repo_path(self):
        random_path = f"/tmp/{uuid.uuid4().hex}"
        dispatcher = RepoHealthDispatcher(random_path)
        self.assertEqual(dispatcher.repo_path, random_path)
        self.assertIsNotNone(dispatcher.repo_health_dashboard)
        self.assertIsNotNone(dispatcher.repo_notifier)

    def test_dispatch_health_and_notify_success(self):
        random_dashboard_data = {uuid.uuid4().hex: random.randint(1, 100)}
        
        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as MockDashboardClass, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as MockNotifierClass:
            
            mock_dashboard = MockDashboardClass.return_value
            mock_dashboard.generate_dashboard.return_value = random_dashboard_data
            mock_dashboard.export_dashboard.return_value = True

            mock_notifier = MockNotifierClass.return_value
            mock_notifier.notify.return_value = True

            result = self.dispatcher.dispatch_health_and_notify(self.file_path)

            self.assertTrue(result)
            MockDashboardClass.assert_called_with(self.repo_path)
            mock_dashboard.generate_dashboard.assert_called_once()
            mock_dashboard.export_dashboard.assert_called_with(self.file_path)
            MockNotifierClass.assert_called_with(self.repo_path)
            mock_notifier.notify.assert_called_with(self.file_path)

    def test_dispatch_health_and_notify_export_fails(self):
        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as MockDashboardClass, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as MockNotifierClass:
            
            mock_dashboard = MockDashboardClass.return_value
            mock_dashboard.generate_dashboard.return_value = {}
            mock_dashboard.export_dashboard.return_value = False

            result = self.dispatcher.dispatch_health_and_notify(self.file_path)

            self.assertFalse(result)
            mock_dashboard.export_dashboard.assert_called_with(self.file_path)
            MockNotifierClass.assert_not_called()

    def test_process_stream_and_dispatch_success(self):
        random_stream_content = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(random_stream_content)

        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as MockDashboardClass, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as MockNotifierClass:
            
            mock_dashboard = MockDashboardClass.return_value
            mock_notifier = MockNotifierClass.return_value
            mock_notifier.notify.return_value = True

            result = self.dispatcher.process_stream_and_dispatch(stream, self.file_path)

            self.assertTrue(result)
            mock_dashboard.process_stream.assert_called_with(stream)
            mock_dashboard.export_dashboard.assert_called_with(self.file_path)
            mock_notifier.notify.assert_called_with(self.file_path)

    def test_check_and_notify_critical_success(self):
        random_title = uuid.uuid4().hex
        random_value = random.randint(500, 1000)
        random_widget_str = f"widget_{uuid.uuid4().hex}"

        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as MockDashboardClass, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as MockNotifierClass:
            
            mock_dashboard = MockDashboardClass.return_value
            mock_dashboard.render_widget.return_value = random_widget_str

            mock_notifier = MockNotifierClass.return_value
            mock_notifier.notify_and_commit.return_value = True

            result = self.dispatcher.check_and_notify_critical(random_title, random_value, self.file_path)

            self.assertTrue(result)
            mock_dashboard.render_widget.assert_called_with(random_title, random_value)
            
            self.assertTrue(os.path.exists(self.file_path))
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, random_widget_str)

            mock_notifier.notify_and_commit.assert_called_once()

    def test_dispatch_calls_dispatch_health_and_notify(self):
        expected_report_path = f"{self.repo_path}/report.json"

        with patch.object(self.dispatcher, "dispatch_health_and_notify", return_value=True) as mock_dispatch:
            result = self.dispatcher.dispatch()

            self.assertTrue(result)
            mock_dispatch.assert_called_once_with(expected_report_path)


if __name__ == "__main__":
    unittest.main()