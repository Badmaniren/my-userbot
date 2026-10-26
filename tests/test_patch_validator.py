import unittest
import io
import ast
import uuid
import random
from unittest.mock import patch, MagicMock
from skills.patch_validator import PatchValidator, PatchValidatorError, validate_patch


class TestPatchValidatorInquisition(unittest.TestCase):

    def setUp(self):
        self.validator = PatchValidator()
        self.patch_id = uuid.uuid4().hex
        self.target_file = f"module_{uuid.uuid4().hex[:6]}.py"
        self.random_func_name = f"func_{uuid.uuid4().hex[:8]}"

    def test_validate_structure_success(self):
        payload = {
            "patch_id": self.patch_id,
            "target_file": self.target_file,
            "content": f"def {self.random_func_name}():\n    pass"
        }
        result = self.validator.validate_structure(payload)
        self.assertTrue(result)

    def test_validate_structure_missing_keys(self):
        payload = {
            "patch_id": self.patch_id,
            "content": "pass"
        }
        with self.assertRaises(PatchValidatorError):
            self.validator.validate_structure(payload)

    def test_validate_structure_invalid_type(self):
        with self.assertRaises(PatchValidatorError):
            self.validator.validate_structure([self.patch_id, self.target_file])

    def test_validate_syntax_success(self):
        code_str = f"def {self.random_func_name}():\n    return {random.randint(1, 100)}"
        stream = io.BytesIO(code_str.encode('utf-8'))
        result = self.validator.validate_syntax(stream)
        self.assertTrue(result)

    def test_validate_syntax_error(self):
        bad_code = f"def {self.random_func_name}(\n    invalid syntax"
        stream = io.BytesIO(bad_code.encode('utf-8'))
        with self.assertRaises(PatchValidatorError):
            self.validator.validate_syntax(stream)

    def test_validate_security_success(self):
        code_content = f"x = {random.randint(1, 500)}\ndef {self.random_func_name}(val):\n    return val + x"
        result = self.validator.validate_security(code_content)
        self.assertTrue(result)

    def test_validate_security_forbidden_call_exec(self):
        code_content = f"exec('{uuid.uuid4().hex}')"
        with self.assertRaises(PatchValidatorError) as ctx:
            self.validator.validate_security(code_content)
        self.assertIn("Forbidden function call: exec", str(ctx.exception))

    def test_validate_security_forbidden_call_eval(self):
        code_content = f"eval('{random.randint(1, 100)} + {random.randint(1, 100)}')"
        with self.assertRaises(PatchValidatorError) as ctx:
            self.validator.validate_security(code_content)
        self.assertIn("Forbidden function call: eval", str(ctx.exception))

    def test_validate_security_forbidden_import_os(self):
        code_content = f"import os\nos.system('echo {uuid.uuid4().hex}')"
        with self.assertRaises(PatchValidatorError) as ctx:
            self.validator.validate_security(code_content)
        self.assertIn("Forbidden import: os", str(ctx.exception))

    def test_validate_security_forbidden_import_from_os(self):
        code_content = f"from os import path\nprint(path.exists('{uuid.uuid4().hex}'))"
        with self.assertRaises(PatchValidatorError) as ctx:
            self.validator.validate_security(code_content)
        self.assertIn("Forbidden import from os", str(ctx.exception))

    def test_validate_patch_integration_success(self):
        code_content = f"def {self.random_func_name}():\n    return '{uuid.uuid4().hex}'"
        payload = {
            "patch_id": self.patch_id,
            "target_file": self.target_file,
            "content": code_content
        }
        result = self.validator.validate_patch(payload)
        self.assertTrue(result)

    def test_wrapper_validate_patch_dict(self):
        code_content = f"def {self.random_func_name}():\n    return {random.randint(100, 999)}"
        payload = {
            "patch_id": self.patch_id,
            "target_file": self.target_file,
            "content": code_content
        }
        result = validate_patch(payload)
        self.assertTrue(result)

    def test_wrapper_validate_patch_str_starts_with_number(self):
        num_prefix = random.randint(1, 9)
        code_str = f"def {num_prefix}{uuid.uuid4().hex[:6]}():\n    pass"
        result = validate_patch(code_str)
        self.assertTrue(result)

    def test_wrapper_validate_patch_arbitrary_input(self):
        arbitrary_input = random.randint(1000, 9999)
        result = validate_patch(arbitrary_input)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()