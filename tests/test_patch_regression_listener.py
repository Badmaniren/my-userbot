import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import os
import io

from skills.patch_regression_listener import (
    PatchRegressionListenerError,
    PatchRegressionListener,
    listen_for_patches,
    start_regression_listening
)

class TestPatchRegressionListener(unittest.TestCase):

    def setUp(self):
        self.watch_dir = uuid.uuid4().hex
        self.callback_arg = uuid.uuid4().hex
        self.mock_callback = lambda data: f"processed_{data}_{uuid.uuid4().hex}"
        self.listener = PatchRegressionListener(self.watch_dir, callback=self.mock_callback)

    def test_listener_lifecycle(self):
        self.assertFalse(self.listener.is_running)
        start_res = self.listener.start_listening()
        self.assertTrue(self.listener.is_running)
        self.assertTrue(start_res)

        stop_res = self.listener.stop_listening()
        self.assertFalse(self.listener.is_running)
        self.assertFalse(stop_res)

    def test_trigger_regression_success(self):
        patch_data = uuid.uuid4().hex
        result = self.listener.trigger_regression(patch_data)
        self.assertIn(patch_data, result)
        self.assertTrue(result.startswith("processed_"))

    def test_trigger_regression_empty_data_raises_error(self):
        for empty_val in ["", None, [], {}]:
            with self.subTest(empty_val=empty_val):
                with self.assertRaises(PatchRegressionListenerError):
                    self.listener.trigger_regression(empty_val)

    def test_trigger_regression_no_callback(self):
        listener_no_cb = PatchRegressionListener(self.watch_dir)
        patch_data = uuid.uuid4().hex
        res = listener_no_cb.trigger_regression(patch_data)
        self.assertTrue(res)

    def test_listen_for_patches(self):
        target_path = uuid.uuid4().hex
        res = listen_for_patches(target_path)
        self.assertIsInstance(res, list)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[1], target_path)
        self.assertIsInstance(res[0], str)
        self.assertEqual(len(res[0]), 32)

    def test_start_regression_listening_with_log(self):
        patch_id = uuid.uuid4().hex
        repo_path = uuid.uuid4().hex
        log_path = f"{uuid.uuid4().hex}.log"
        file_target = uuid.uuid4().hex

        payload = {
            "patch_id": patch_id,
            "repo_path": repo_path,
            "log_path": log_path,
            "file_target": file_target
        }

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = start_regression_listening(payload)

        m_open.assert_called_once_with(log_path, "w", encoding="utf-8")
        handle = m_open()
        expected_log_content = f"Processed patch {patch_id} for repo {repo_path}\n"
        handle.write.assert_called_once_with(expected_log_content)

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("patch_id"), patch_id)
        self.assertEqual(result.get("file_target"), file_target)

    def test_start_regression_listening_without_log(self):
        patch_id = uuid.uuid4().hex
        repo_path = uuid.uuid4().hex
        file_target = uuid.uuid4().hex

        payload = {
            "patch_id": patch_id,
            "repo_path": repo_path,
            "file_target": file_target
        }

        with patch("builtins.open") as m_open:
            result = start_regression_listening(payload)
            m_open.assert_not_called()

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("patch_id"), patch_id)
        self.assertEqual(result.get("file_target"), file_target)

if __name__ == "__main__":
    unittest.main()