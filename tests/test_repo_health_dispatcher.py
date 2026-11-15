import unittest
from unittest.mock import patch, mock_open
import io
import os
import uuid
import random
import string
from skills.repo_health_dispatcher import RepoHealthDispatcher


class TestRepoHealthDispatcher(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.dispatcher = RepoHealthDispatcher(self.repo_path)

    def test_init_sets_attributes(self):
        self.assertEqual(self.dispatcher.repo_path, self.repo_path)
        self.assertIsNotNone(self.dispatcher.repo_health_dashboard)
        self.assertIsNotNone(self.dispatcher.repo_notifier)

    def test_notify_with_retry_success_on_first_try(self):
        mock_func = unittest.mock.Mock(return_value=True)
        arg1 = uuid.uuid4().hex
        kwarg1 = uuid.uuid4().hex

        result = self.dispatcher._notify_with_retry(mock_func, arg1, key=kwarg1)

        self.assertTrue(result)
        mock_func.assert_called_once_with(arg1, key=kwarg1)

    def test_notify_with_retry_success_on_retry(self):
        mock_func = unittest.mock.Mock(side_effect=[False, False, True])
        arg1 = uuid.uuid4().hex

        result = self.dispatcher._notify_with_retry(mock_func, arg1)

        self.assertTrue(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_notify_with_retry_all_fails(self):
        mock_func = unittest.mock.Mock(return_value=False)
        arg1 = uuid.uuid4().hex

        result = self.dispatcher._notify_with_retry(mock_func, arg1)

        self.assertFalse(result)
        self.assertEqual(mock_func.call_count, 3)

    def test_dispatch_health_and_notify_success(self):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        with patch.object(self.dispatcher.repo_health_dashboard, 'generate_dashboard') as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, 'export_dashboard', return_value=True) as mock_exp, \
             patch.object(self.dispatcher, '_notify_with_retry', return_value=True) as mock_retry:

            result = self.dispatcher.dispatch_health_and_notify(file_path)

            self.assertTrue(result)
            mock_gen.assert_called_once()
            mock_exp.assert_called_once_with(file_path)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify, file_path)

    def test_dispatch_health_and_notify_export_fail(self):
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        
        with patch.object(self.dispatcher.repo_health_dashboard, 'generate_dashboard') as mock_gen, \
             patch.object(self.dispatcher.repo_health_dashboard, 'export_dashboard', return_value=False) as mock_exp, \
             patch.object(self.dispatcher, '_notify_with_retry') as mock_retry:

            result = self.dispatcher.dispatch_health_and_notify(file_path)

            self.assertFalse(result)
            mock_gen.assert_called_once()
            mock_exp.assert_called_once_with(file_path)
            mock_retry.assert_not_called()

    def test_process_stream_and_dispatch_with_string(self):
        stream_str = uuid.uuid4().hex
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"

        with patch.object(self.dispatcher.repo_health_dashboard, 'process_stream') as mock_proc, \
             patch.object(self.dispatcher.repo_health_dashboard, 'export_dashboard', return_value=True) as mock_exp, \
             patch.object(self.dispatcher, '_notify_with_retry', return_value=True) as mock_retry:

            result = self.dispatcher.process_stream_and_dispatch(stream_str, file_path)

            self.assertTrue(result)
            mock_proc.assert_called_once()
            args, _ = mock_proc.call_args
            self.assertIsInstance(args[0], io.BytesIO)
            self.assertEqual(args[0].read().decode("utf-8"), stream_str)
            mock_exp.assert_called_once_with(file_path)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify, file_path)

    def test_process_stream_and_dispatch_with_bytes_io(self):
        stream_bytes = io.BytesIO(uuid.uuid4().hex.encode("utf-8"))
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"

        with patch.object(self.dispatcher.repo_health_dashboard, 'process_stream') as mock_proc, \
             patch.object(self.dispatcher.repo_health_dashboard, 'export_dashboard', return_value=False) as mock_exp, \
             patch.object(self.dispatcher, '_notify_with_retry') as mock_retry:

            result = self.dispatcher.process_stream_and_dispatch(stream_bytes, file_path)

            self.assertFalse(result)
            mock_proc.assert_called_once_with(stream_bytes)
            mock_exp.assert_called_once_with(file_path)
            mock_retry.assert_not_called()

    def test_check_and_notify_critical(self):
        title = uuid.uuid4().hex
        value = random.randint(100, 999)
        file_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt"
        rendered_widget = uuid.uuid4().hex

        with patch.object(self.dispatcher.repo_health_dashboard, 'render_widget', return_value=rendered_widget) as mock_render, \
             patch("builtins.open", new_callable=mock_open) as mock_file, \
             patch.object(self.dispatcher, '_notify_with_retry', return_value=True) as mock_retry:

            result = self.dispatcher.check_and_notify_critical(title, value, file_path)

            self.assertTrue(result)
            mock_render.assert_called_once_with(title, value)
            mock_file.assert_called_once_with(file_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(rendered_widget)
            mock_retry.assert_called_once_with(self.dispatcher.repo_notifier.notify_and_commit)

    def test_dispatch(self):
        expected_path = os.path.join(self.repo_path, "report.json")

        with patch.object(self.dispatcher, 'dispatch_health_and_notify', return_value=True) as mock_dispatch_hn:
            result = self.dispatcher.dispatch()

            self.assertTrue(result)
            mock_dispatch_hn.assert_called_once_with(expected_path)


if __name__ == "__main__":
    unittest.main()