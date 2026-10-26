import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import ast

from skills.patch_validator import PatchValidator, PatchValidatorError


class TestPatchValidator(unittest.TestCase):

    def setUp(self):
        self.validator = PatchValidator()
        self.random_salt = uuid.uuid4().hex
        self.random_code_valid = f"def func_{self.random_salt}():\n    x = {random.randint(1, 100)}\n    return x"
        self.random_code_syntax_error = f"def func_{self.random_salt}(\n    pass"
        self.random_code_unsafe = f"import os\nos.system('{uuid.uuid4().hex}')"

    def test_validate_syntax_success(self):
        result = self.validator.validate_syntax(self.random_code_valid)
        self.assertTrue(result)

    def test_validate_syntax_failure(self):
        with self.assertRaises(PatchValidatorError) as ctx:
            self.validator.validate_syntax(self.random_code_syntax_error)
        self.assertIn("Syntax", str(ctx.exception))

    def test_validate_safety_success(self):
        result = self.validator.validate_safety(self.random_code_valid)
        self.assertTrue(result)

    def test_validate_safety_failure(self):
        with self.assertRaises(PatchValidatorError) as ctx:
            self.validator.validate_safety(self.random_code_unsafe)
        self.assertIn("Security", str(ctx.exception))

    def test_validate_patch_complete_flow(self):
        patch_data = f"--- a/{uuid.uuid4().hex}.py\n+++ b/{uuid.uuid4().hex}.py\n@@ -1,1 +1,2 @@\n-# comment\n+x = {random.randint(100, 999)}"
        is_valid = self.validator.validate_patch(patch_data)
        self.assertTrue(is_valid)

    def test_validate_patch_with_io_stream(self):
        stream_content = f"print('{uuid.uuid4().hex}')".encode('utf-8')
        mock_stream = io.BytesIO(stream_content)

        result = self.validator.validate_stream(mock_stream)
        self.assertTrue(result)

    def test_custom_exception_inheritance(self):
        err_msg = uuid.uuid4().hex
        err = PatchValidatorError(err_msg)
        self.assertIsInstance(err, Exception)
        self.assertEqual(str(err), err_msg)


if __name__ == '__main__':
    unittest.main()