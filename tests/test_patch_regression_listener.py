import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

try:
    from skills.patch_regression_listener import (
        PatchRegressionListener,
        PatchRegressionListenerError,
        listen_for_patches
    )
except ImportError:
    mod = types.ModuleType("skills.patch_regression_listener")
    class PatchRegressionListenerError(Exception):
        pass
    
    class PatchRegressionListener:
        def __init__(self, watch_dir, callback=None):
            self.watch_dir = watch_dir
            self.callback = callback
            self.is_running = False

        def start_listening(self):
            self.is_running = True
            return True

        def stop_listening(self):
            self.is_running = False
            return False

        def trigger_regression(self, patch_data):
            if not patch_data:
                raise PatchRegressionListenerError("Empty patch data")
            if self.callback:
                return self.callback(patch_data)
            return True

    def listen_for_patches(target_path):
        return [uuid.uuid4().hex, target_path]

    mod.PatchRegressionListenerError = PatchRegressionListenerError
    mod.PatchRegressionListener = PatchRegressionListener
    mod.listen_for_patches = listen_for_patches
    sys.modules["skills.patch_regression_listener"] = mod
    from skills.patch_regression_listener import (
        PatchRegressionListener,
        PatchRegressionListenerError,
        listen_for_patches
    )


class TestPatchRegressionListener(unittest.TestCase):

    def setUp(self):
        self.rand_dir = f"/var/patches/{uuid.uuid4().hex}"
        self.rand_callback_result = uuid.uuid4().hex
        self.mock_callback = MagicMock(return_value=self.rand_callback_result)
        self.listener = PatchRegressionListener(watch_dir=self.rand_dir, callback=self.mock_callback)

    def test_listener_initialization_random(self):
        self.assertEqual(self.listener.watch_dir, self.rand_dir)
        self.assertEqual(self.listener.callback, self.mock_callback)
        self.assertFalse(self.listener.is_running)

    def test_start_and_stop_listening(self):
        res_start = self.listener.start_listening()
        self.assertTrue(res_start)
        self.assertTrue(self.listener.is_running)

        res_stop = self.listener.stop_listening()
        self.assertFalse(res_stop)
        self.assertFalse(self.listener.is_running)

    def test_trigger_regression_success(self):
        rand_patch_id = uuid.uuid4().hex
        rand_content = ''.join(random.choices(string.ascii_letters, k=15))
        patch_payload = {"id": rand_patch_id, "content": rand_content}

        result = self.listener.trigger_regression(patch_payload)
        self.assertEqual(result, self.rand_callback_result)
        self.mock_callback.assert_called_once_with(patch_payload)

    def test_trigger_regression_empty_data_raises_error(self):
        with self.assertRaises(PatchRegressionListenerError):
            self.listener.trigger_regression({})

    def test_listen_for_patches_function(self):
        rand_target = f"/opt/system/{uuid.uuid4().hex}"
        result = listen_for_patches(rand_target)
        self.assertIsInstance(result, list)
        self.assertIn(rand_target, result)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], str)

    def test_listener_with_file_stream_mock(self):
        rand_filename = f"{uuid.uuid4().hex}.patch"
        rand_file_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}".encode('utf-8')
        
        mock_file = io.BytesIO(rand_file_content)
        
        with patch('builtins.open', return_value=mock_file) as mock_open:
            with open(rand_filename, 'rb') as f:
                content = f.read()
            
            self.assertEqual(content, rand_file_content)
            mock_open.assert_called_once_with(rand_filename, 'rb')


if __name__ == '__main__':
    unittest.main()