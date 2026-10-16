import ast
import io
import os
import random
import string
import tempfile
import unittest
from unittest.mock import MagicMock, mock_open, patch
import uuid

from skills.code_validator import (
    ASTValidationError,
    CodeValidator,
    CodeValidatorError,
)


def _generate_random_identifier(length=8):
    return random.choice(string.ascii_lowercase) + "".join(
        random.choices(string.ascii_letters + string.digits, k=length - 1)
    )


def _generate_valid_python_code():
    func_name = _generate_random_identifier(10)
    var_a = _generate_random_identifier(6)
    var_b = _generate_random_identifier(6)
    val_a = random.randint(1, 1000)
    val_b = random.randint(1, 1000)
    return (
        f"def {func_name}():\n"
        f"    {var_a} = {val_a}\n"
        f"    {var_b} = {val_b}\n"
        f"    return {var_a} + {var_b}\n",
        func_name,
        val_a + val_b,
    )


def _generate_invalid_python_code():
    var_name = _generate_random_identifier(8)
    junk = "".join(random.choices("!@#$%^&*()_+=-`~[]{}|;:',.<>/?", k=12))
    return f"def {var_name}(:\n    {junk} = {junk}\n"


class TestCodeValidator(unittest.TestCase):
    def setUp(self):
        self.random_repo = f"/tmp/repo_{uuid.uuid4().hex}"
        self.validator = CodeValidator(repo_path=self.random_repo)

    def test_initialization_with_random_repo(self):
        random_repo_path = f"/var/repos/{uuid.uuid4().hex}"
        custom_forbidden = [_generate_random_identifier(7) for _ in range(4)]
        validator = CodeValidator(
            repo_path=random_repo_path,
            forbidden_nodes=custom_forbidden,
            max_complexity=random.randint(10, 50),
        )
        self.assertEqual(validator.repo_path, random_repo_path)
        for pattern in custom_forbidden:
            self.assertIn(pattern, validator.forbidden_nodes)

    def test_validate_syntax_valid_code(self):
        code, func_name, _ = _generate_valid_python_code()
        result = self.validator.validate_syntax(code)
        self.assertIsInstance(result, bool)
        self.assertTrue(result)

    def test_validate_syntax_invalid_code_raises_or_fails(self):
        invalid_code = _generate_invalid_python_code()
        with self.assertRaises((CodeValidatorError, ASTValidationError, SyntaxError)):
            self.validator.validate_syntax(invalid_code)

    def test_validate_syntax_empty_string(self):
        empty_code = "   \n\t  \n"
        result = self.validator.validate_syntax(empty_code)
        self.assertIsInstance(result, bool)

    def test_validate_ast_detects_forbidden_eval(self):
        random_var = _generate_random_identifier(8)
        random_payload = f"'{uuid.uuid4().hex}'"
        code = f"{random_var} = eval({random_payload})\n"
        report = self.validator.validate_ast(code)
        self.assertIsInstance(report, dict)
        self.assertIn("is_valid", report)
        self.assertFalse(report["is_valid"])
        self.assertIn("violations", report)
        violations_str = str(report["violations"])
        self.assertTrue(
            "eval" in violations_str or "Call" in violations_str
        )

    def test_validate_ast_detects_forbidden_exec(self):
        random_var = _generate_random_identifier(7)
        random_payload = f"'{uuid.uuid4().hex}'"
        code = f"def {random_var}():\n    exec({random_payload})\n"
        report = self.validator.validate_ast(code)
        self.assertIsInstance(report, dict)
        self.assertFalse(report["is_valid"])
        self.assertTrue(
            any("exec" in str(v) for v in report.get("violations", []))
        )

    def test_validate_ast_custom_forbidden_function(self):
        forbidden_fn = _generate_random_identifier(10)
        custom_validator = CodeValidator(
            repo_path=self.random_repo,
            forbidden_nodes=[forbidden_fn],
        )
        random_arg = uuid.uuid4().hex
        code = f"{forbidden_fn}('{random_arg}')\n"
        report = custom_validator.validate_ast(code)
        self.assertFalse(report["is_valid"])
        violations_str = str(report["violations"])
        self.assertIn(forbidden_fn, violations_str)

    def test_validate_ast_clean_code_passes(self):
        code, func_name, expected_sum = _generate_valid_python_code()
        report = self.validator.validate_ast(code)
        self.assertIsInstance(report, dict)
        self.assertTrue(report.get("is_valid", False))
        self.assertEqual(len(report.get("violations", [])), 0)

    def test_validate_file_success(self):
        code, func_name, _ = _generate_valid_python_code()
        random_filename = f"test_{uuid.uuid4().hex}.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, random_filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)

            report = self.validator.validate_file(file_path)
            self.assertIsInstance(report, dict)
            self.assertTrue(report.get("is_valid"))
            self.assertEqual(report.get("file_path"), file_path)

    def test_validate_file_not_found(self):
        ghost_path = f"/tmp/ghost_{uuid.uuid4().hex}.py"
        with self.assertRaises((CodeValidatorError, FileNotFoundError)):
            self.validator.validate_file(ghost_path)

    def test_validate_file_invalid_syntax_in_file(self):
        invalid_code = _generate_invalid_python_code()
        random_filename = f"corrupt_{uuid.uuid4().hex}.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, random_filename)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(invalid_code)

            report = self.validator.validate_file(file_path)
            self.assertIsInstance(report, dict)
            self.assertFalse(report.get("is_valid"))
            self.assertIn("error", report)

    def test_check_complexity_linear_code(self):
        code, _, _ = _generate_valid_python_code()
        complexity = self.validator.check_complexity(code)
        self.assertIsInstance(complexity, int)
        self.assertGreaterEqual(complexity, 1)

    def test_check_complexity_deeply_nested_branches(self):
        nesting_depth = random.randint(4, 8)
        var_name = _generate_random_identifier(6)
        code_lines = [f"def complex_{_generate_random_identifier(5)}({var_name}):"]
        indent = "    "
        for i in range(nesting_depth):
            cond_val = random.randint(1, 100)
            code_lines.append(f"{indent * (i + 1)}if {var_name} > {cond_val}:")
        code_lines.append(f"{indent * (nesting_depth + 1)}return {var_name}")

        nested_code = "\n".join(code_lines) + "\n"
        complexity = self.validator.check_complexity(nested_code)
        self.assertIsInstance(complexity, int)
        self.assertGreaterEqual(complexity, nesting_depth)

    def test_validate_ast_exceeding_max_complexity(self):
        max_c = random.randint(2, 4)
        strict_validator = CodeValidator(
            repo_path=self.random_repo,
            max_complexity=max_c,
        )
        deep_code = "def deeply_nested(x):\n"
        for i in range(max_c + 3):
            deep_code += "    " * (i + 1) + f"if x == {i}:\n"
        deep_code += "    " * (max_c + 4) + "return True\n"

        report = strict_validator.validate_ast(deep_code)
        self.assertFalse(report["is_valid"])
        violations_str = str(report.get("violations", []))
        self.assertTrue(
            "complexity" in violations_str.lower()
            or "max_complexity" in violations_str.lower()
        )

    def test_validate_patch_with_clean_addition(self):
        patch_file = f"src/{_generate_random_identifier(8)}.py"
        random_val = random.randint(100, 999)
        patch_diff = (
            f"--- a/{patch_file}\n"
            f"+++ b/{patch_file}\n"
            f"@@ -1,3 +1,4 @@\n"
            f" def existing():\n"
            f"+    new_var = {random_val}\n"
            f"     return True\n"
        )
        report = self.validator.validate_patch(patch_diff)
        self.assertIsInstance(report, dict)
        self.assertIn("is_valid", report)
        self.assertTrue(report["is_valid"])

    def test_validate_patch_with_syntax_error(self):
        patch_file = f"src/{_generate_random_identifier(8)}.py"
        junk = _generate_invalid_python_code()
        patch_diff = (
            f"--- a/{patch_file}\n"
            f"+++ b/{patch_file}\n"
            f"@@ -1,1 +1,2 @@\n"
            f"+{junk}\n"
        )
        report = self.validator.validate_patch(patch_diff)
        self.assertIsInstance(report, dict)
        self.assertFalse(report["is_valid"])

    def test_batch_validate_mixed_payloads(self):
        valid_code, valid_fn, _ = _generate_valid_python_code()
        invalid_code = _generate_invalid_python_code()
        forbidden_code = f"eval('{uuid.uuid4().hex}')\n"

        key_valid = f"item_valid_{uuid.uuid4().hex}"
        key_invalid = f"item_invalid_{uuid.uuid4().hex}"
        key_forbidden = f"item_forbidden_{uuid.uuid4().hex}"

        items = {
            key_valid: valid_code,
            key_invalid: invalid_code,
            key_forbidden: forbidden_code,
        }

        batch_result = self.validator.batch_validate(items)
        self.assertIsInstance(batch_result, dict)
        self.assertIn(key_valid, batch_result)
        self.assertIn(key_invalid, batch_result)
        self.assertIn(key_forbidden, batch_result)

        self.assertTrue(batch_result[key_valid]["is_valid"])
        self.assertFalse(batch_result[key_invalid]["is_valid"])
        self.assertFalse(batch_result[key_forbidden]["is_valid"])

    def test_validate_stream_success(self):
        code, _, _ = _generate_valid_python_code()
        stream = io.BytesIO(code.encode("utf-8"))
        report = self.validator.validate_stream(stream)
        self.assertIsInstance(report, dict)
        self.assertTrue(report.get("is_valid"))

    def test_validate_stream_with_forbidden_call(self):
        random_cmd = uuid.uuid4().hex
        code = f"__import__('os').system('{random_cmd}')\n"
        stream = io.BytesIO(code.encode("utf-8"))
        report = self.validator.validate_stream(stream)
        self.assertIsInstance(report, dict)
        self.assertFalse(report.get("is_valid"))

    def test_add_forbidden_rule_dynamically(self):
        custom_func = _generate_random_identifier(12)
        code = f"def worker():\n    {custom_func}()\n"
        initial_check = self.validator.validate_ast(code)
        self.assertTrue(initial_check["is_valid"])

        self.validator.add_forbidden_rule(custom_func)
        subsequent_check = self.validator.validate_ast(code)
        self.assertFalse(subsequent_check["is_valid"])
        self.assertIn(custom_func, str(subsequent_check.get("violations", [])))

    def test_mocked_file_reading_with_patch(self):
        file_path = f"/mock/path/{uuid.uuid4().hex}.py"
        code, _, expected_val = _generate_valid_python_code()

        with patch("builtins.open", mock_open(read_data=code)) as mock_file:
            report = self.validator.validate_file(file_path)
            mock_file.assert_called_once_with(file_path, "r", encoding="utf-8")
            self.assertTrue(report["is_valid"])

    def test_validate_ast_with_mocked_parser_failure(self):
        code, _, _ = _generate_valid_python_code()
        error_msg = f"Simulated parse anomaly {uuid.uuid4().hex}"
        with patch("ast.parse", side_effect=ValueError(error_msg)):
            with self.assertRaises((CodeValidatorError, ValueError)):
                self.validator.validate_ast(code)


if __name__ == "__main__":
    unittest.main()