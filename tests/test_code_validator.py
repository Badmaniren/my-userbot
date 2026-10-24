import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import ast

from skills.code_validator import (
    CodeValidatorError,
    CodeValidatorAntipatternError,
    CodeValidatorASTError,
    CodeValidator
)


class TestCodeValidatorInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.validator = CodeValidator(repo_path=self.repo_path)
        self.random_forbidden_word = f"forbidden_{uuid.uuid4().hex[:6]}"
        self.validator.add_forbidden_construct(self.random_forbidden_word)

    def test_validator_initialization(self):
        dynamic_path = f"/var/tmp/{uuid.uuid4().hex}"
        validator_instance = CodeValidator(repo_path=dynamic_path)
        self.assertEqual(validator_instance.repo_path, dynamic_path)
        self.assertIsInstance(validator_instance.forbidden_constructs, set)
        self.assertIn(self.random_forbidden_word, self.validator.forbidden_constructs)

    def test_add_forbidden_construct_success(self):
        new_pattern = f"exec_{uuid.uuid4().hex[:8]}"
        initial_count = len(self.validator.forbidden_constructs)
        self.validator.add_forbidden_construct(new_pattern)
        self.assertIn(new_pattern, self.validator.forbidden_constructs)
        self.assertEqual(len(self.validator.forbidden_constructs), initial_count + 1)

    def test_validate_ast_structure_valid(self):
        var_name = f"var_{uuid.uuid4().hex[:6]}"
        func_name = f"func_{uuid.uuid4().hex[:6]}"
        valid_code = f"def {func_name}():\n    {var_name} = {random.randint(1, 100)}\n    return {var_name}"
        
        result = self.validator.validate_code(valid_code)
        self.assertTrue(result)

    def test_validate_ast_structure_invalid_syntax(self):
        malformed_code = f"def func_{uuid.uuid4().hex[:6]}():\n    print(unclosed_string"

        with self.assertRaises(CodeValidatorASTError):
            self.validator.validate_code(malformed_code)

    def test_validate_code_antipattern_detected(self):
        var_name = f"var_{uuid.uuid4().hex[:6]}"
        malicious_code = f"def compute():\n    {self.random_forbidden_word}()\n    {var_name} = {random.randint(10, 99)}"

        with self.assertRaises(CodeValidatorAntipatternError) as ctx:
            self.validator.validate_code(malicious_code)
        self.assertIn(self.random_forbidden_word, str(ctx.exception))

    def test_validate_stream_valid(self):
        literal_val = random.randint(100, 999)
        stream_content = f"x = {literal_val}\nprint(x)"
        stream = io.BytesIO(stream_content.encode('utf-8'))

        result = self.validator.validate_stream(stream)
        self.assertTrue(result)

    def test_validate_stream_antipattern(self):
        stream_content = f"# Some comment\n{self.random_forbidden_word}({random.randint(1, 5)})"
        stream = io.BytesIO(stream_content.encode('utf-8'))

        with self.assertRaises(CodeValidatorAntipatternError):
            self.validator.validate_stream(stream)

    def test_batch_validate_patches(self):
        batch_id = uuid.uuid4().hex
        valid_code_1 = f"val_a = {random.randint(1, 50)}"
        valid_code_2 = f"val_b = {random.randint(51, 100)}"
        invalid_code = f"{self.random_forbidden_word}()"

        patch_batch = {
            f"patch_{uuid.uuid4().hex[:4]}": valid_code_1,
            f"patch_{uuid.uuid4().hex[:4]}": valid_code_2,
            f"patch_{uuid.uuid4().hex[:4]}": invalid_code
        }

        results = self.validator.batch_validate(patch_batch)
        self.assertIsInstance(results, dict)
        self.assertIn("failed", results)
        self.assertIn("passed", results)
        self.assertEqual(len(results["failed"]), 1)
        self.assertEqual(len(results["passed"]), 2)

    def test_custom_ast_visitor_integration(self):
        target_name = f"restricted_{uuid.uuid4().hex[:5]}"
        self.validator.add_forbidden_construct(target_name)

        code_snippet = f"""
class CustomClass_{uuid.uuid4().hex[:8]}:
    def run(self):
        {target_name}()
"""
        with self.assertRaises(CodeValidatorAntipatternError):
            self.validator.validate_code(code_snippet)


if __name__ == '__main__':
    unittest.main()