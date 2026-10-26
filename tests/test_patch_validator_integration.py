import unittest
import uuid
import random
from skills.patch_validator import PatchValidator, PatchValidatorError, validate_patch


class TestPatchValidatorIntegration(unittest.TestCase):

    def setUp(self):
        self.validator = PatchValidator()
        self.random_id = str(uuid.uuid4())
        self.target_file = f"module_{random.randint(1000, 9999)}.py"

    def test_validate_patch_success_integration(self):
        safe_code = f"def compute_{self.random_id.replace('-', '_')}():\n    return {random.randint(1, 100)}"
        patch_payload = {
            "patch_id": self.random_id,
            "target_file": self.target_file,
            "content": safe_code
        }

        result = self.validator.validate_patch(patch_payload)
        self.assertTrue(result)

        wrapper_result = validate_patch(patch_payload)
        self.assertTrue(wrapper_result)

    def test_validate_patch_structure_error_integration(self):
        invalid_payload = {
            "patch_id": self.random_id,
            "content": "print('test')"
        }

        with self.assertRaises(PatchValidatorError):
            self.validator.validate_patch(invalid_payload)

    def test_validate_patch_syntax_error_integration(self):
        syntax_broken_code = f"def {self.random_id.replace('-', '_')}():\n    return " + "print('unclosed"
        patch_payload = {
            "patch_id": self.random_id,
            "target_file": self.target_file,
            "content": syntax_broken_code
        }

        with self.assertRaises(PatchValidatorError):
            self.validator.validate_patch(patch_payload)

    def test_validate_patch_security_forbidden_call_integration(self):
        forbidden_func = random.choice(['exec', 'eval'])
        unsafe_code = f"{forbidden_func}('print({random.randint(1, 100)})')"
        patch_payload = {
            "patch_id": self.random_id,
            "target_file": self.target_file,
            "content": unsafe_code
        }

        with self.assertRaises(PatchValidatorError):
            self.validator.validate_patch(patch_payload)

    def test_validate_patch_security_forbidden_import_integration(self):
        unsafe_code = "import os\nos.system('echo test')"
        patch_payload = {
            "patch_id": self.random_id,
            "target_file": self.target_file,
            "content": unsafe_code
        }

        with self.assertRaises(PatchValidatorError):
            self.validator.validate_patch(patch_payload)

    def test_validate_patch_security_forbidden_import_from_integration(self):
        unsafe_code = "from os import path\nprint(path.exists('.'))"
        patch_payload = {
            "patch_id": self.random_id,
            "target_file": self.target_file,
            "content": unsafe_code
        }

        with self.assertRaises(PatchValidatorError):
            self.validator.validate_patch(patch_payload)

    def test_validate_patch_string_input_integration(self):
        code_string = f"def func_{random.randint(100, 999)}():\n    x = {random.randint(10, 50)}\n    return x"
        result = validate_patch(code_string)
        self.assertTrue(result)

    def test_validate_patch_string_input_with_number_prefix_integration(self):
        code_string = f"def 8invalid_{random.randint(100, 999)}():\n    return {random.randint(1, 9)}"
        result = validate_patch(code_string)
        self.assertTrue(result)

    def test_validate_patch_arbitrary_type_integration(self):
        arbitrary_input = random.randint(10000, 99999)
        result = validate_patch(arbitrary_input)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()