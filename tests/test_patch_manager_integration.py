import unittest
import uuid
import random
import tempfile
import pathlib
from skills.patch_manager import PatchManager
from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator
from skills.patch_autocorrector import PatchAutocorrector

class TestPatchManagerIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.random_id = str(uuid.uuid4())
        self.patch_manager = PatchManager(repo_path=self.repo_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_composition_and_correction(self):
        random_var_name = f"var_{self.random_id.replace('-', '_')}"
        malformed_code = f"x = 1\n{random_var_name} = 'test'\n"

        result = self.patch_manager.process_patch(malformed_code)

        self.assertIsInstance(result, str)
        self.assertIn(random_var_name, result)

    def test_pipeline_with_invalid_syntax(self):
        invalid_code = f"def broken_func({self.random_id}:"

        with self.assertRaises(Exception):
            self.patch_manager.process_patch(invalid_code)

if __name__ == '__main__':
    unittest.main()