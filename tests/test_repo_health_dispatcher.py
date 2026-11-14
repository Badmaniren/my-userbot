import io
import os
import random
import string
import unittest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid4().hex}/{uuid4().hex}"
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def test_init_creates_dependencies(self):
        rand_path = f"/repo/{uuid4().hex}"
        with patch("skills.repo_health_dispatcher.RepoHealthDashboard") as mock_dash, \
             patch("skills.repo_health_dispatcher.RepoNotifier") as mock_notif:
            
            dispatcher = RepoHealthDispatcher(rand_path)
            self.assertEqual(dispatcher.repo_path, rand_path)
            mock_dash.assert_called_once_with(rand_path)
            mock_notif.assert_called_once_with(rand_path)

    def test_dispatch_health_and_notify_success(self):
        target_file = f"/{uuid4().hex}/{uuid4().hex}.json"
        
        with patch.object(self.dispatcher.repo_health_dashboard, "generate_dashboard") as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=True) as mock_exp, \
             patch.object(self.dispatcher.repo_notifier, "notify", return_value=True) as mock_notif:
            
            result = self.dispatcher.dispatch_health_and_notify(target_file)
            
            self.assertTrue(result)
            mock_gen.assert_called_once()
            mock_exp.assert_called_once_with(target_file)
            mock_notif.assert_called_once_with(target_file)

    def test_dispatch_health_and_notify_export_failed(self):
        target_file = f"/{uuid4().hex}/{uuid4().hex}.json"
        
        with patch.object(self.dispatcher.repo_health_dashboard, "generate_dashboard") as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=False) as mock_exp, \
             patch.object(self.dispatcher.repo_notifier, "notify") as mock_notif:
            
            result = self.dispatcher.dispatch_health_and_notify(target_file)
            
            self.assertFalse(result)
            mock_gen.assert_called_once()
            mock_exp.assert_called_once_with(target_file)
            mock_notif.assert_not_called()

    def test_process_stream_and_dispatch_with_string_stream(self):
        random_content = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        target_file = f"/{uuid4().hex}/{uuid4().hex}.json"
        
        with patch.object(self.dispatcher.repo_health_dashboard, "process_stream") as mock_proc, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard") as mock_exp, \
             patch.object(self.dispatcher.repo_notifier, "notify", return_value=True) as mock_notif:
            
            result = self.dispatcher.process_stream_and_dispatch(random_content, target_file)
            
            self.assertTrue(result)
            mock_proc.assert_called_once()
            
            passed_stream = mock_proc.call_args[0][0]
            self.assertIsInstance(passed_stream, io.BytesIO)
            self.assertEqual(passed_stream.read(), random_content.encode("utf-8"))
            
            mock_exp.assert_called_once_with(target_file)
            mock_notif.assert_called_once_with(target_file)

    def test_process_stream_and_dispatch_with_bytes_stream(self):
        random_bytes = uuid4().hex.encode("utf-8")
        stream = io.BytesIO(random_bytes)
        target_file = f"/{uuid4().hex}/{uuid4().hex}.json"
        
        with patch.object(self.dispatcher.repo_health_dashboard, "process_stream") as mock_proc, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard") as mock_exp, \
             patch.object(self.dispatcher.repo_notifier, "notify", return_value=False) as mock_notif:
            
            result = self.dispatcher.process_stream_and_dispatch(stream, target_file)
            
            self.assertFalse(result)
            mock_proc.assert_called_once_with(stream)
            mock_exp.assert_called_once_with(target_file)
            mock_notif.assert_called_once_with(target_file)

    def test_check_and_notify_critical(self):
        title = uuid4().hex
        value = random.randint(100, 999)
        target_file = f"/{uuid4().hex}/{uuid4().hex}.txt"
        rendered_widget = f"WIDGET_{uuid4().hex}_{value}"

        with patch.object(self.dispatcher.repo_health_dashboard, "render_widget", return_value=rendered_widget) as mock_render, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch.object(self.dispatcher.repo_notifier, "notify_and_commit", return_value=True) as mock_commit:

            result = self.dispatcher.check_and_notify_critical(title, value, target_file)

            self.assertTrue(result)
            mock_render.assert_called_once_with(title, value)
            mock_file.assert_called_once_with(target_file, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(rendered_widget)
            mock_commit.assert_called_once()

    def test_dispatch(self):
        expected_path = os.path.join(self.repo_path, "report.json")

        with patch.object(self.dispatcher, "dispatch_health_and_notify", return_value=True) as mock_dispatch_hn:
            result = self.dispatcher.dispatch()

            self.assertTrue(result)
            mock_dispatch_hn.assert_called_once_with(expected_path)


if __name__ == "__main__":
    unittest.main()