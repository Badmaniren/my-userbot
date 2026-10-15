import unittest
from unittest.mock import patch, mock_open
import ast
import os
import random
import uuid
import io

from skills.code_validator import CodeValidator, CodeValidatorError


class TestCodeValidator(unittest.TestCase):
    def setUp(self):
        self.validator = CodeValidator()
        self.rand_str = uuid.uuid4().hex
        self.rand_func_name = f"func_{uuid.uuid4().hex[:6]}"
        self.rand_class_name = f"Class{uuid.uuid4().hex[:6].capitalize()}"

    def test_validate_syntax_valid(self):
        code = f"def {self.rand_func_name}():\n    x = {random.randint(1, 100)}\n    return x"
        result = self.validator.validate_syntax(code)
        self.assertTrue(result)

    def test_validate_syntax_invalid(self):
        code = f"def {self.rand_func_name}(\n    x = {random.randint(1, 100)}"
        with self.assertRaises(CodeValidatorError):
            self.validator.validate_syntax(code)

    def test_detect_empty_except_pass(self):
        code = f"""
try:
    val = {random.randint(1, 100)}
except Exception:
    pass
"""
        empty_excepts = self.validator.detect_empty_except(code)
        self.assertTrue(len(empty_excepts) > 0)

    def test_detect_empty_except_ellipsis(self):
        code = f"""
try:
    val = {random.randint(1, 100)}
except Exception:
    ...
"""
        empty_excepts = self.validator.detect_empty_except(code)
        self.assertTrue(len(empty_excepts) > 0)

    def test_detect_empty_except_none(self):
        rnd_msg = uuid.uuid4().hex
        code = f"""
try:
    val = {random.randint(1, 100)}
except Exception as e:
    raise RuntimeError("{rnd_msg}")
"""
        empty_excepts = self.validator.detect_empty_except(code)
        self.assertEqual(empty_excepts, [])

    def test_detect_empty_except_syntax_error(self):
        code = f"except Exception:\n    pass"
        with self.assertRaises(CodeValidatorError):
            self.validator.detect_empty_except(code)

    def test_analyze_structure(self):
        code = f"""
class {self.rand_class_name}:
    def method(self):
        return {random.randint(1, 100)}

def {self.rand_func_name}():
    return {random.randint(1, 100)}
"""
        structure = self.validator.analyze_structure(code)
        self.assertIn(self.rand_class_name, structure["classes"])
        self.assertIn(self.rand_func_name, structure["functions"])

    def test_analyze_structure_syntax_error(self):
        code = f"class {self.rand_class_name}"
        with self.assertRaises(CodeValidatorError):
            self.validator.analyze_structure(code)

    def test_validate_code(self):
        code = f"""
class {self.rand_class_name}:
    def method(self):
        try:
            x = {random.randint(1, 100)}
        except:
            pass
        return x

def {self.rand_func_name}():
    return 42
"""
        report = self.validator.validate_code(code)
        self.assertTrue(report["is_valid"])
        self.assertTrue(len(report["empty_excepts"]) > 0)
        self.assertIn(self.rand_class_name, report["structure"]["classes"])
        self.assertIn(self.rand_func_name, report["structure"]["functions"])

    def test_validate_method(self):
        code = f"x = {random.randint(1, 100)}"
        res = self.validator.validate(code)
        self.assertTrue(res["syntax_valid"])
        self.assertEqual(res["empty_except_blocks"], [])

    def test_validate_file_not_found(self):
        non_existent_path = f"/tmp/{uuid.uuid4().hex}.py"
        with self.assertRaises(CodeValidatorError):
            self.validator.validate_file(non_existent_path)

    def test_validate_file_io_error(self):
        file_path = f"/tmp/{uuid.uuid4().hex}.py"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", side_effect=IOError("Random disk failure")):
            with self.assertRaises(CodeValidatorError):
                self.validator.validate_file(file_path)

    def test_validate_file_success(self):
        file_path = f"/tmp/{uuid.uuid4().hex}.py"
        valid_code = f"def {self.rand_func_name}(): pass"
        with patch("os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=valid_code)):
            report = self.validator.validate_file(file_path)
            self.assertTrue(report["is_valid"])
            self.assertIn(self.rand_func_name, report["structure"]["functions"])