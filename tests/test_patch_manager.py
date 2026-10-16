import unittest
from unittest.mock import MagicMock
import tempfile
import uuid

from skills.patch_manager import PatchManager


class TestPatchManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.patch_manager = PatchManager(repo_path=self.repo_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initialization(self):
        pm = PatchManager(repo_path=self.repo_path)
        self.assertEqual(pm.repo_path, self.repo_path)
        self.assertIsNotNone(pm.sanitizer)
        self.assertIsNotNone(pm.validator)
        self.assertIsNotNone(pm.autocorrector)

    def test_process_patch_valid_code(self):
        code = "a = 10\nb = 20\nc = a + b"
        result = self.patch_manager.process_patch(code)
        self.assertIn("a = 10", result)
        self.assertIn("c = a + b", result)

    def test_process_patch_invalid_syntax_raises_error(self):
        invalid_code = "def foo(x:"
        with self.assertRaises(Exception):
            self.patch_manager.process_patch(invalid_code)

    def test_process_patch_autocorrection_flow(self):
        pm = PatchManager(repo_path=self.repo_path)

        # Mock validator to fail first time, then pass after correction
        pm.validator.validate = MagicMock(side_effect=[False, True])
        pm.autocorrector.correct = MagicMock(return_value="x = 1")

        result = pm.process_patch("x = 1")

        self.assertEqual(result, "x = 1")
        pm.autocorrector.correct.assert_called_once()
        self.assertEqual(pm.validator.validate.call_count, 2)

    def test_process_patch_autocorrection_fails_raises_value_error(self):
        pm = PatchManager(repo_path=self.repo_path)

        # Mock validator to fail both times
        pm.validator.validate = MagicMock(return_value=False)
        pm.autocorrector.correct = MagicMock(return_value="x = 2")

        with self.assertRaises(ValueError) as ctx:
            pm.process_patch("x = 1")

        self.assertIn("Patch validation and correction failed", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
