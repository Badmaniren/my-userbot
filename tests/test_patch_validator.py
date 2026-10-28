import unittest
from unittest.mock import patch, MagicMock
import ast
import io
import os
import subprocess
import uuid
import random
import string

from skills.patch_validator import PatchValidator, PatchValidatorError


class TestPatchValidator(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.validator = PatchValidator(repo_path=self.repo_path)

    def test_validate_syntax_success(self):
        var_name = f"var_{uuid.uuid4().hex[:8]}"
        val_int = random.randint(100, 999)
        code_str = f"{var_name} = {val_int}\nprint({var_name})"

        result = self.validator.validate_syntax(code_str)
        self.assertTrue(result)

    def test_validate_syntax_failure(self):
        bad_syntax = f"print('{uuid.uuid4().hex}"
        with self.assertRaises(PatchValidatorError) as ctx:
            self.validator.validate_syntax(bad_syntax)
        self.assertIn("Invalid syntax", str(ctx.exception))

    def test_perform_security_check_success(self):
        func_name = f"func_{uuid.uuid4().hex[:6]}"
        ret_val = uuid.uuid4().hex
        code_str = f"def {func_name}():\n    return '{ret_val}'"

        result = self.validator.perform_security_check(code_str)
        self.assertTrue(result)

    def test_perform_security_check_dangerous_import(self):
        mod_name = random.choice(['os', 'sys', 'subprocess', 'shutil', 'pickle'])
        code_str = f"import {mod_name}\n{mod_name}.system('echo')"

        with self.assertRaises(PatchValidatorError) as ctx:
            self.validator.perform_security_check(code_str)
        self.assertIn("Dangerous import detected", str(ctx.exception))

    def test_perform_security_check_dangerous_import_from(self):
        mod_name = random.choice(['os', 'sys', 'subprocess', 'shutil', 'pickle'])
        attr_name = f"attr_{uuid.uuid4().hex[:5]}"
        code_str = f"from {mod_name} import {attr_name}"

        with self.assertRaises(PatchValidatorError) as ctx:
            self.validator.perform_security_check(code_str)
        self.assertIn("Dangerous import detected", str(ctx.exception))

    def test_perform_security_check_syntax_error(self):
        bad_code = f"x = [1, 2, {uuid.uuid4().hex}"
        with self.assertRaises(PatchValidatorError) as ctx:
            self.validator.perform_security_check(bad_code)
        self.assertIn("Syntax error during security check", str(ctx.exception))

    def test_apply_and_test_diff_success(self):
        diff_content = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\n" + \
                       f"--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,1 @@\n-{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"

        with patch('subprocess.run') as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_run.return_value = mock_process

            result = self.validator.apply_and_test_diff(diff_content)
            self.assertTrue(result)
            mock_run.assert_called_once()

    def test_apply_and_test_diff_failure(self):
        diff_content = f"invalid diff content {uuid.uuid4().hex}"
        err_output = f"error: patch failed: {uuid.uuid4().hex}"

        with patch('subprocess.run') as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stderr.decode.return_value = err_output
            mock_run.return_value = mock_process

            with self.assertRaises(PatchValidatorError) as ctx:
                self.validator.apply_and_test_diff(diff_content)
            self.assertIn("Failed to apply diff", str(ctx.exception))

    def test_apply_and_test_diff_exception(self):
        diff_content = uuid.uuid4().hex
        with patch('subprocess.run', side_effect=OSError(f"OS Error {uuid.uuid4().hex}")):
            with self.assertRaises(PatchValidatorError) as ctx:
                self.validator.apply_and_test_diff(diff_content)
            self.assertIn("Error applying diff", str(ctx.exception))

    def test_read_patch_stream(self):
        file_path = f"/tmp/{uuid.uuid4().hex}.patch"
        file_content = f"# Patch {uuid.uuid4().hex}\nprint('{uuid.uuid4().hex}')"

        mock_file = unittest.mock.mock_open(read_data=file_content)
        with patch('builtins.open', mock_file):
            content = self.validator.read_patch_stream(file_path)
            self.assertEqual(content, file_content)
            mock_file.assert_called_once_with(file_path, 'r', encoding='utf-8')

    def test_validate_patch_flow(self):
        sanitizer = MagicMock()
        sanitized_content = f"x = {random.randint(1, 100)}"
        sanitizer.sanitize.return_value = sanitized_content

        git_inspector = MagicMock()

        validator = PatchValidator(
            repo_path=self.repo_path,
            patch_sanitizer=sanitizer,
            git_inspector=git_inspector
        )

        raw_patch = f"import {uuid.uuid4().hex}"
        result = validator.validate_patch(raw_patch)

        sanitizer.sanitize.assert_called_once_with(raw_patch)
        self.assertTrue(result.is_valid)


if __name__ == '__main__':
    unittest.main()