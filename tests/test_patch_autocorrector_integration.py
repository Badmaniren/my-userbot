import unittest
import uuid
import tempfile
import os
from skills.patch_autocorrector import PatchAutocorrector
from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator

class TestPatchAutocorrectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.sanitizer = CodeSanitizer(repo_path=self.repo_path)
        self.validator = CodeValidator(repo_path=self.repo_path)
        self.autocorrector = PatchAutocorrector(
            repo_path=self.repo_path,
            sanitizer=self.sanitizer,
            validator=self.validator
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_patch_autocorrector_pipeline(self):
        unique_id = str(uuid.uuid4())
        variable_name = f"var_{uuid.uuid4().hex[:8]}"
        
        malformed_patch = f"""
try:
    {variable_name} = "{unique_id}"
    print({variable_name})
except Exception:
    pass
"""
        
        corrected_code = self.autocorrector.correct_and_validate(malformed_patch)
        
        self.assertIsInstance(corrected_code, str)
        self.assertTrue(len(corrected_code) > 0)
        
        is_valid = self.validator.validate_code(corrected_code)
        self.assertTrue(is_valid, "Autocorrected code must pass validation")

if __name__ == "__main__":
    unittest.main()