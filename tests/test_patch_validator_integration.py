import unittest
import uuid
import random
import io
from skills.patch_validator import PatchValidator, sandbox_exec

class TestPatchValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.validator = PatchValidator()
        self.random_id = str(uuid.uuid4())
        self.random_val = random.randint(1000, 99999)

    def test_integration_valid_patch_execution(self):
        expected_result = f"result_{self.random_id}_{self.random_val}"
        valid_code = f"""
def execute_patch():
    return "{expected_result}"
"""
        result = self.validator.verify_patch(valid_code)
        self.assertTrue(result.get("passed"))
        self.assertTrue(result.get("static_passed"))
        self.assertTrue(result.get("dynamic_passed"))

        stream = io.BytesIO(valid_code.encode('utf-8'))
        stream_result = self.validator.verify_stream(stream)
        self.assertTrue(stream_result.get("passed"))

        dict_valid = self.validator.validate({"code": valid_code})
        self.assertTrue(dict_valid)

        str_valid = self.validator.validate(valid_code)
        self.assertTrue(str_valid)

    def test_integration_forbidden_import_static_fail(self):
        forbidden_mod = random.choice(list(self.validator.forbidden_modules))
        invalid_code = f"""
import {forbidden_mod}

def execute_patch():
    return {forbidden_mod}.__name__
"""
        result = self.validator.verify_patch(invalid_code)
        self.assertFalse(result.get("passed"))
        self.assertFalse(result.get("static_passed"))
        self.assertFalse(result.get("dynamic_passed"))

        self.assertFalse(self.validator.validate(invalid_code))

    def test_integration_syntax_error_fail(self):
        invalid_syntax_code = f"""
def execute_patch()
    return {self.random_val}
"""
        static_res = self.validator.analyze_static(invalid_syntax_code)
        self.assertFalse(static_res.get("is_valid"))
        self.assertIn("SyntaxError", static_res.get("error"))

        result = self.validator.verify_patch(invalid_syntax_code)
        self.assertFalse(result.get("passed"))

    def test_integration_sandbox_runtime_error(self):
        runtime_err_code = f"""
def execute_patch():
    raise ValueError("Error_{self.random_id}")
"""
        static_res = self.validator.analyze_static(runtime_err_code)
        self.assertTrue(static_res.get("is_valid"))

        dynamic_res = self.validator.analyze_dynamic(runtime_err_code)
        self.assertFalse(dynamic_res.get("executed"))
        self.assertIn(f"Error_{self.random_id}", dynamic_res.get("error"))

        result = self.validator.verify_patch(runtime_err_code)
        self.assertFalse(result.get("passed"))
        self.assertTrue(result.get("static_passed"))
        self.assertFalse(result.get("dynamic_passed"))

if __name__ == "__main__":
    unittest.main()