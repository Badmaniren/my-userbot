import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from skills.patch_validator import PatchValidator, PatchValidatorError


class TestPatchValidatorInquisitor(unittest.TestCase):

    def setUp(self):
        self.random_patch_id = uuid.uuid4().hex
        self.random_code_snippet = f"def func_{uuid.uuid4().hex[:8]}():\n    pass # {uuid.uuid4().hex}"
        self.random_file_path = f"/tmp/{uuid.uuid4().hex}.py"
        self.random_error_msg = uuid.uuid4().hex

    def test_patch_validator_initialization_success(self):
        validator = PatchValidator(repo_path=self.random_file_path)
        self.assertEqual(validator.repo_path, self.random_file_path)

    def test_validate_patch_syntax_valid(self):
        validator = PatchValidator(repo_path=self.random_file_path)
        with patch('skills.patch_validator.open', create=True) as mock_open:
            mock_open.return_value = io.BytesIO(self.random_code_snippet.encode('utf-8'))
            result = validator.validate_syntax(self.random_file_path)
            self.assertTrue(result)

    def test_validate_patch_syntax_invalid_raises_error(self):
        validator = PatchValidator(repo_path=self.random_file_path)
        invalid_code = f"def func_{uuid.uuid4().hex[:8]}(:\n    syntax_error"
        with patch('skills.patch_validator.open', create=True) as mock_open:
            mock_open.return_value = io.BytesIO(invalid_code.encode('utf-8'))
            with self.assertRaises(PatchValidatorError) as ctx:
                validator.validate_syntax(self.random_file_path)
            self.assertIn("Syntax", str(ctx.exception))

    def test_secure_pipeline_execution_success(self):
        validator = PatchValidator(repo_path=self.random_file_path)
        mock_diff = f"--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,1 %>\n-{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"

        with patch('skills.patch_validator.subprocess.run') as mock_subproc:
            mock_subproc.return_value.returncode = 0
            mock_subproc.return_value.stdout = mock_diff.encode('utf-8')

            status = validator.run_pipeline(self.random_patch_id)
            self.assertTrue(status)
            mock_subproc.assert_called()

    def test_secure_pipeline_execution_failure(self):
        validator = PatchValidator(repo_path=self.random_file_path)
        with patch('skills.patch_validator.subprocess.run') as mock_subproc:
            mock_subproc.return_value.returncode = random.randint(1, 255)
            mock_subproc.return_value.stderr = self.random_error_msg.encode('utf-8')

            with self.assertRaises(PatchValidatorError):
                validator.run_pipeline(self.random_patch_id)

    def test_sanitization_check_malicious_payload(self):
        validator = PatchValidator(repo_path=self.random_file_path)
        dangerous_code = f"import os; os.system('{uuid.uuid4().hex}')"

        with patch('skills.patch_validator.open', create=True) as mock_open:
            mock_open.return_value = io.BytesIO(dangerous_code.encode('utf-8'))
            with self.assertRaises(PatchValidatorError) as ctx:
                validator.inspect_security_risks(self.random_file_path)
            self.assertIsNotNone(str(ctx.exception))


if __name__ == '__main__':
    unittest.main()