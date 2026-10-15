import unittest
import uuid
import random
import os
import tempfile
from skills.code_validator import CodeValidator, CodeValidatorError

class TestCodeValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.validator = CodeValidator()
        self.test_dir = tempfile.TemporaryDirectory()
        self.random_tag = uuid.uuid4().hex[:8]

    def tearDown(self):
        self.test_dir.cleanup()

    def test_code_validator_integration_flow(self):
        func_name = f"func_{self.random_tag}"
        class_name = f"Class_{self.random_tag}"
        metric_val = random.randint(10, 100)

        valid_code = f"""
import os
import sys

class {class_name}:
    def __init__(self):
        self.val = {metric_val}

def {func_name}():
    try:
        x = 1 / 0
    except ZeroDivisionError:
        pass
    return {metric_val}
"""

        syntax_res = self.validator.validate_syntax(valid_code)
        self.assertTrue(syntax_res)

        empty_excepts = self.validator.detect_empty_except(valid_code)
        self.assertIsInstance(empty_excepts, list)
        self.assertTrue(len(empty_excepts) > 0)

        structure = self.validator.analyze_structure(valid_code)
        self.assertIn(class_name, structure["classes"])
        self.assertIn(func_name, structure["functions"])

        full_report = self.validator.validate_code(valid_code)
        self.assertTrue(full_report["is_valid"])
        self.assertEqual(full_report["structure"]["classes"], [class_name])
        self.assertEqual(full_report["structure"]["functions"], [func_name])

        compat_report = self.validator.validate(valid_code)
        self.assertTrue(compat_report["syntax_valid"])
        self.assertEqual(compat_report["empty_except_blocks"], empty_excepts)

        file_name = f"test_file_{self.random_tag}.py"
        file_path = os.path.join(self.test_dir.name, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(valid_code)

        file_report = self.validator.validate_file(file_path)
        self.assertTrue(file_report["is_valid"])
        self.assertEqual(file_report["structure"]["classes"], [class_name])
        self.assertEqual(file_report["structure"]["functions"], [func_name])

    def test_code_validator_invalid_syntax_integration(self):
        invalid_code = f"""
def broken_{self.random_tag}()
    print("missing colon")
"""
        with self.assertRaises(CodeValidatorError):
            self.validator.validate_syntax(invalid_code)

        with self.assertRaises(CodeValidatorError):
            self.validator.detect_empty_except(invalid_code)

        with self.assertRaises(CodeValidatorError):
            self.validator.analyze_structure(invalid_code)

        full_report = self.validator.validate_code(invalid_code)
        self.assertFalse(full_report["is_valid"])

        compat_report = self.validator.validate(invalid_code)
        self.assertFalse(compat_report["syntax_valid"])

        non_existent_file = os.path.join(self.test_dir.name, f"non_existent_{self.random_tag}.py")
        with self.assertRaises(CodeValidatorError):
            self.validator.validate_file(non_existent_file)

if __name__ == "__main__":
    unittest.main()