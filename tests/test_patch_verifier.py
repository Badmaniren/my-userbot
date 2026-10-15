import unittest
from unittest.mock import patch, MagicMock
import ast
import io
import random
import uuid
import string

from skills.patch_verifier import PatchVerifier, PatchVerifierError

class TestPatchVerifier(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/repo/{uuid.uuid4().hex}"
        self.verifier = PatchVerifier(self.random_repo_path)

    def test_verify_patch_syntax_valid(self):
        func_name = f"func_{uuid.uuid4().hex[:8]}"
        var_name = f"var_{uuid.uuid4().hex[:8]}"
        random_value = random.randint(100, 999)

        valid_code = f"def {func_name}():\n    {var_name} = {random_value}\n    return {var_name}"

        result = self.verifier.verify_syntax(valid_code)
        self.assertTrue(result)

    def test_verify_patch_syntax_invalid(self):
        random_garbage = ''.join(random.choices(string.ascii_letters, k=15))
        invalid_code = f"def {random_garbage}():\n    if True\n        print({random.randint(1, 10)})"

        with self.assertRaises(PatchVerifierError):
            self.verifier.verify_syntax(invalid_code)

    def test_anticheat_restricted_imports(self):
        forbidden_module = random.choice(["os", "sys", "subprocess", "shutil", "eval", "exec"])
        dangerous_code = f"import {forbidden_module}\n\ndef exploit():\n    return {forbidden_module}.getcwd()"

        with self.assertRaises(PatchVerifierError) as ctx:
            self.verifier.verify_security_constraints(dangerous_code)

        self.assertIn(forbidden_module, str(ctx.exception))

    def test_anticheat_eval_exec_banned(self):
        dangerous_builtin = random.choice(["eval", "exec", "compile", "__import__"])
        payload = f"def run_payload():\n    return {dangerous_builtin}('{random.randint(1, 100)}') "

        with self.assertRaises(PatchVerifierError):
            self.verifier.verify_security_constraints(payload)

    def test_apply_patch_verification_success(self):
        expected_ret = random.randint(1000, 9999)
        patch_code = f"def compute_{uuid.uuid4().hex[:6]}():\n    return {expected_ret}"

        mock_file_content = io.BytesIO(patch_code.encode('utf-8'))

        with patch('skills.patch_verifier.open', return_value=mock_file_content), \
             patch('os.path.exists', return_value=True):

            random_file_path = f"modules/{uuid.uuid4().hex}.py"
            verification_result = self.verifier.verify_and_approve(random_file_path)
            self.assertTrue(verification_result)

    def test_verify_ast_node_limit_exceeded(self):
        massive_code_lines = []
        func_name = f"heavy_{uuid.uuid4().hex[:6]}"
        massive_code_lines.append(f"def {func_name}():")

        num_statements = random.randint(1500, 2500)
        for i in range(num_statements):
            massive_code_lines.append(f"    x_{i} = {random.randint(1, 100)}")
        massive_code_lines.append("    return x_0")

        massive_code = "\n".join(massive_code_lines)

        with self.assertRaises(PatchVerifierError):
            self.verifier.verify_ast_complexity(massive_code)

    def test_verify_file_read_error(self):
        non_existent_path = f"/invalid/path/{uuid.uuid4().hex}.py"

        with patch('skills.patch_verifier.open', side_effect=FileNotFoundError):
            with self.assertRaises(PatchVerifierError):
                self.verifier.verify_and_approve(non_existent_path)