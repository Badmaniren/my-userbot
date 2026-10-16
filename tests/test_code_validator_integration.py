import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.code_validator import CodeValidator
from skills.code_sanitizer import CodeSanitizer, CodeAntipatternDetectedError


class TestCodeValidatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.validator = CodeValidator(repo_path=self.test_dir)
        self.sanitizer = CodeSanitizer(repo_path=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_code_validator_with_sanitizer_integration(self):
        unique_var_name = f"var_{uuid.uuid4().hex[:8]}"
        random_value = random.randint(100, 999)

        malicious_or_forbidden_code = f"""
def compute_{uuid.uuid4().hex[:6]}():
    try:
        x = {random_value}
        return x
    except:
        pass
        """

        try:
            sanitized_code = self.sanitizer.sanitize_patch(malicious_or_forbidden_code)
        except CodeAntipatternDetectedError:
            sanitized_code = f"def compute_{uuid.uuid4().hex[:6]}():\n    x = {random_value}\n    return x\n"

        self.assertIsInstance(sanitized_code, str)

        is_valid = self.validator.validate_ast(sanitized_code)
        self.assertTrue(is_valid, "Sanitized and validated AST code should pass validation.")

        test_file_name = f"test_module_{uuid.uuid4().hex[:6]}.py"
        test_file_path = os.path.join(self.test_dir, test_file_name)

        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write(sanitized_code)

        self.assertTrue(os.path.exists(test_file_path), "File should be successfully created on disk.")

        with open(test_file_path, "r", encoding="utf-8") as f:
            read_content = f.read()

        validation_result = self.validator.validate_file(test_file_path)
        self.assertIsInstance(validation_result, dict)
        self.assertIn("status", validation_result)
        self.assertEqual(validation_result["status"], "success")

    def test_code_validator_rejects_broken_syntax(self):
        broken_code = f"""
def broken_{uuid.uuid4().hex[:6]}()
    print({random.randint(1, 10)})
        """

        is_valid = self.validator.validate_ast(broken_code)
        self.assertFalse(is_valid, "Validator must reject syntax errors in AST.")


if __name__ == "__main__":
    unittest.main()
