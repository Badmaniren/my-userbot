import unittest
import uuid
import os
import tempfile
from skills.patch_regression_listener import (
    PatchRegressionListener,
    PatchRegressionListenerError,
    listen_for_patches,
    start_regression_listening
)
from skills.git_inspector import GitInspector

class TestPatchRegressionListenerIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.watch_dir = self.temp_dir.name
        self.patch_id = uuid.uuid4().hex
        self.repo_path = self.watch_dir
        self.log_path = os.path.join(self.watch_dir, f"regression_{uuid.uuid4().hex}.log")
        self.file_target = f"module_{uuid.uuid4().hex}.py"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_listener_lifecycle_and_callback(self):
        callback_invoked = []
        def dummy_callback(data):
            callback_invoked.append(data)
            return f"processed_{data.get('id')}"

        listener = PatchRegressionListener(watch_dir=self.watch_dir, callback=dummy_callback)
        self.assertTrue(listener.start_listening())
        self.assertTrue(listener.is_running)

        test_data = {"id": self.patch_id, "status": "pending"}
        result = listener.trigger_regression(test_data)
        
        self.assertEqual(result, f"processed_{self.patch_id}")
        self.assertIn(test_data, callback_invoked)

        self.assertFalse(listener.stop_listening())
        self.assertFalse(listener.is_running)

    def test_trigger_regression_empty_data_raises_error(self):
        listener = PatchRegressionListener(watch_dir=self.watch_dir)
        with self.assertRaises(PatchRegressionListenerError):
            listener.trigger_regression({})

    def test_listen_for_patches_integration(self):
        patches = listen_for_patches(self.file_target)
        self.assertIsInstance(patches, list)
        self.assertEqual(len(patches), 2)
        self.assertEqual(patches[1], self.file_target)
        self.assertIsInstance(patches[0], str)

    def test_start_regression_listening_writes_log_and_returns_payload(self):
        payload = {
            "patch_id": self.patch_id,
            "repo_path": self.repo_path,
            "log_path": self.log_path,
            "file_target": self.file_target
        }

        result = start_regression_listening(payload)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["patch_id"], self.patch_id)
        self.assertEqual(result["file_target"], self.file_target)

        self.assertTrue(os.path.exists(self.log_path))
        with open(self.log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        self.assertIn(self.patch_id, log_content)
        self.assertIn(self.repo_path, log_content)

    def test_git_inspector_integration_with_listener_env(self):
        inspector = GitInspector(repo_path=self.watch_dir)
        history = inspector.get_commit_history(max_count=5)
        self.assertIsInstance(history, list)

        analysis = inspector.analyze_repository()
        self.assertIsNotNone(analysis)

if __name__ == "__main__":
    unittest.main()