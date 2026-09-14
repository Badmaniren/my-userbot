import unittest
import io
import uuid
import random
from skills.patch_validator import PatchValidator, sandbox_exec


class TestPatchValidator(unittest.TestCase):

    def setUp(self):
        self.validator = PatchValidator()
        self.rand_suffix = uuid.uuid4().hex[:8]

    def test_sandbox_exec_success(self):
        rand_val = random.randint(1000, 9999)
        code = f"""
def execute_patch():
    return {rand_val}
"""
        success, res, err = sandbox_exec(code)
        self.assertTrue(success)
        self.assertEqual(res, rand_val)
        self.assertEqual(err, "")

    def test_sandbox_exec_syntax_error(self):
        rand_syntax_error_code = f"def execute_patch(\n    return {random.randint(1, 100)}"
        success, res, err = sandbox_exec(rand_syntax_error_code)
        self.assertFalse(success)
        self.assertIsNone(res)
        self.assertTrue(len(err) > 0)

    def test_analyze_static_valid(self):
        rand_var = f"var_{self.rand_suffix}"
        rand_val = random.randint(10, 100)
        code = f"""
def execute_patch():
    {rand_var} = {rand_val}
    return {rand_var}
"""
        result = self.validator.analyze_static(code)
        self.assertTrue(result["is_valid"])
        self.assertIsNone(result["error"])

    def test_analyze_static_syntax_error(self):
        code = f"print('{self.rand_suffix}'"
        result = self.validator.analyze_static(code)
        self.assertFalse(result["is_valid"])
        self.assertIn("SyntaxError", result["error"])

    def test_analyze_static_forbidden_import(self):
        forbidden = random.choice(list(self.validator.forbidden_modules))
        code = f"""
import {forbidden}
def execute_patch():
    return '{self.rand_suffix}'
"""
        result = self.validator.analyze_static(code)
        self.assertFalse(result["is_valid"])
        self.assertIn(f"Forbidden import: {forbidden}", result["error"])

    def test_analyze_static_forbidden_import_from(self):
        forbidden = random.choice(list(self.validator.forbidden_modules))
        code = f"""
from {forbidden} import something
def execute_patch():
    return '{self.rand_suffix}'
"""
        result = self.validator.analyze_static(code)
        self.assertFalse(result["is_valid"])
        self.assertIn(f"Forbidden import: {forbidden}", result["error"])

    def test_analyze_static_forbidden_call(self):
        forbidden = random.choice(list(self.validator.forbidden_modules))
        code = f"""
def execute_patch():
    return {forbidden}('{self.rand_suffix}')
"""
        result = self.validator.analyze_static(code)
        self.assertFalse(result["is_valid"])
        self.assertIn(f"Forbidden call: {forbidden}", result["error"])

    def test_analyze_dynamic_valid(self):
        rand_res = uuid.uuid4().hex
        code = f"""
def execute_patch():
    return "{rand_res}"
"""
        result = self.validator.analyze_dynamic(code)
        self.assertTrue(result["executed"])
        self.assertEqual(result["result"], rand_res)

    def test_analyze_dynamic_runtime_error(self):
        code = """
def execute_patch():
    raise ValueError("runtime_fail")
"""
        result = self.validator.analyze_dynamic(code)
        self.assertFalse(result["executed"])
        self.assertIn("runtime_fail", result["error"])

    def test_verify_patch_all_pass(self):
        rand_num = random.randint(500, 1000)
        code = f"""
def execute_patch():
    return {rand_num}
"""
        res = self.validator.verify_patch(code)
        self.assertTrue(res["passed"])
        self.assertTrue(res["static_passed"])
        self.assertTrue(res["dynamic_passed"])

    def test_verify_patch_static_fail(self):
        code = f"""
import os
def execute_patch():
    return '{self.rand_suffix}'
"""
        res = self.validator.verify_patch(code)
        self.assertFalse(res["passed"])
        self.assertFalse(res["static_passed"])
        self.assertFalse(res["dynamic_passed"])

    def test_verify_patch_dynamic_fail(self):
        code = """
def execute_patch():
    raise RuntimeError("fail_dynamic")
"""
        res = self.validator.verify_patch(code)
        self.assertFalse(res["passed"])
        self.assertTrue(res["static_passed"])
        self.assertFalse(res["dynamic_passed"])

    def test_verify_stream(self):
        rand_str = uuid.uuid4().hex
        code = f"""
def execute_patch():
    return "{rand_str}"
"""
        stream = io.BytesIO(code.encode('utf-8'))
        res = self.validator.verify_stream(stream)
        self.assertTrue(res["passed"])
        self.assertTrue(res["static_passed"])
        self.assertTrue(res["dynamic_passed"])

    def test_validate_with_string(self):
        rand_val = random.randint(1, 100)
        code = f"""
def execute_patch():
    return {rand_val}
"""
        is_valid = self.validator.validate(code)
        self.assertTrue(is_valid)

    def test_validate_with_dict(self):
        rand_msg = uuid.uuid4().hex
        patch_dict = {
            "code": f"""
def execute_patch():
    return "{rand_msg}"
"""
        }
        is_valid = self.validator.validate(patch_dict)
        self.assertTrue(is_valid)

    def test_validate_with_invalid_type(self):
        invalid_data = [random.randint(1, 50), uuid.uuid4().hex]
        is_valid = self.validator.validate(invalid_data)
        self.assertFalse(is_valid)