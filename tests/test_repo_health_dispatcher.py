import io
import os
import random
import unittest
import uuid
from unittest.mock import MagicMock, patch
from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):
    def setUp(self):
        self.repo_path = os.path.join("/tmp", uuid.uuid4().hex)
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def test_dispatch_health_and_notify_success(self):
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")

        with patch.object(self.dispatcher.repo_health_dashboard, "generate_dashboard") as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=True) as mock_exp, \
             patch.object(self.dispatcher.repo_notifier, "notify", return_value=True) as mock_not:

            result = self.dispatcher.dispatch_health_and_notify(file_path)

            self.assertTrue(result)
            mock_gen.assert_called_once()
            mock_exp.assert_called_once_with(file_path)
            mock_not.assert_called_once_with(file_path)

    def test_dispatch_health_and_notify_export_failure(self):
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")

        with patch.object(self.dispatcher.repo_health_dashboard, "generate_dashboard") as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=False) as mock_exp, \
             patch.object(self.dispatcher.repo_notifier, "notify") as mock_not:

            result = self.dispatcher.dispatch_health_and_notify(file_path)

            self.assertFalse(result)
            mock_gen.assert_called_once()
            mock_exp.assert_called_once_with(file_path)
            mock_not.assert_not_called()

    def test_dispatch_health_and_notify_retry_mechanism(self):
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.json")

        with patch.object(self.dispatcher.repo_health_dashboard, "generate_dashboard"), \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard", return_value=True), \
             patch.object(self.dispatcher.repo_notifier, "notify", side_effect=[False, False, True]) as mock_not:

            result = self.dispatcher.dispatch_health_and_notify(file_path)

            self.assertTrue(result)
            self.assertEqual(mock_not.call_count, 3)

    def test_process_stream_and_dispatch_with_string(self):
        random_string = uuid.uuid4().hex
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.log")

        with patch.object(self.dispatcher.repo_health_dashboard, "process_stream") as mock_proc, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard") as mock_exp, \
             patch.object(self.dispatcher.repo_notifier, "notify", return_value=True) as mock_not:

            result = self.dispatcher.process_stream_and_dispatch(random_string, file_path)

            self.assertTrue(result)
            mock_proc.assert_called_once()
            mock_exp.assert_called_once_with(file_path)
            mock_not.assert_called_once_with(file_path)

    def test_process_stream_and_dispatch_with_bytes_io(self):
        random_bytes = uuid.uuid4().hex.encode("utf-8")
        stream = io.BytesIO(random_bytes)
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.log")

        with patch.object(self.dispatcher.repo_health_dashboard, "process_stream") as mock_proc, \
             patch.object(self.dispatcher.repo_health_dashboard, "export_dashboard") as mock_exp, \
             patch.object(self.dispatcher.repo_notifier, "notify", return_value=True) as mock_not:

            result = self.dispatcher.process_stream_and_dispatch(stream, file_path)

            self.assertTrue(result)
            mock_proc.assert_called_once()
            mock_exp.assert_called_once_with(file_path)
            mock_not.assert_called_once_with(file_path)

    def test_check_and_notify_critical(self):
        title = uuid.uuid4().hex
        value = random.randint(100, 999)
        file_path = os.path.join(self.repo_path, f"{uuid.uuid4().hex}.txt")
        rendered_widget = f"CRITICAL: {title}={value}"

        with patch.object(self.dispatcher.repo_health_dashboard, "render_widget", return_value=rendered_widget) as mock_render, \
             patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file, \
             patch.object(self.dispatcher.repo_notifier, "notify_and_commit", return_value=True) as mock_notify:

            result = self.dispatcher.check_and_notify_critical(title, value, file_path)

            self.assertTrue(result)
            mock_render.assert_called_once_with(title, value)
            mock_file.assert_called_once_with(file_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(rendered_widget)
            mock_notify.assert_called_once()

    def test_dispatch_default(self):
        expected_report_path = os.path.join(self.repo_path, "report.json")

        with patch.object(self.dispatcher, "dispatch_health_and_notify", return_value=True) as mock_dispatch:
            result = self.dispatcher.dispatch()

            self.assertTrue(result)
            mock_dispatch.assert_called_once_with(expected_report_path)


if __name__ == "__main__":
    unittest.main()