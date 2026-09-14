import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import ast
import types

from skills.patch_validator import PatchValidator

class TestPatchValidator(unittest.TestCase):

    def setUp(self):
        self.validator = PatchValidator()
        self.random_module = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_func = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.random_var = ''.join(random.choices(string.ascii_lowercase, k=6))
        self.random_uuid = uuid.uuid4().hex

    def test_static_analysis_valid_syntax(self):
        valid_code = f"def {self.random_func}():\n    {self.random_var} = {random.randint(1, 100)}\n    return {self.random_var}"
        result = self.validator.analyze_static(valid_code)
        self.assertTrue(result.get("is_valid"))
        self.assertEqual(result.get("error"), None)

    def test_static_analysis_syntax_error(self):
        invalid_code = f"def {self.random_func}()\n    return {random.randint(101, 200)}"
        result = self.validator.analyze_static(invalid_code)
        self.assertFalse(result.get("is_valid"))
        self.assertIn("SyntaxError", str(result.get("error")))

    def test_static_analysis_forbidden_imports(self):
        forbidden_modules = ["os", "sys", "subprocess", "shutil", "eval", "exec"]
        chosen_forbidden = random.choice(forbidden_modules)
        malicious_code = f"import {chosen_forbidden}\n\ndef {self.random_func}():\n    pass"
        result = self.validator.analyze_static(malicious_code)
        self.assertFalse(result.get("is_valid"))
        self.assertIn(chosen_forbidden, str(result.get("error")))

    def test_dynamic_analysis_success(self):
        expected_output = random.randint(1000, 9999)
        safe_patch = f"def execute_patch():\n    return {expected_output}"
        
        with patch('skills.patch_validator.sandbox_exec') as mock_sandbox:
            mock_sandbox.return_value = (True, expected_output, "")
            result = self.validator.analyze_dynamic(safe_patch)
            
        self.assertTrue(result.get("executed"))
        self.assertEqual(result.get("result"), expected_output)

    def test_dynamic_analysis_runtime_failure(self):
        error_message = f"RuntimeError_{uuid.uuid4().hex[:8]}"
        failing_patch = f"def execute_patch():\n    raise RuntimeError('{error_message}')"
        
        with patch('skills.patch_validator.sandbox_exec') as mock_sandbox:
            mock_sandbox.return_value = (False, None, error_message)
            result = self.validator.analyze_dynamic(failing_patch)
            
        self.assertFalse(result.get("executed"))
        self.assertIn(error_message, result.get("error"))

    def test_verify_patch_complete_pipeline_success(self):
        patch_content = f"def {self.random_func}():\n    return '{self.random_uuid}'"
        
        with patch('skills.patch_validator.sandbox_exec') as mock_sandbox:
            mock_sandbox.return_value = (True, self.random_uuid, "")
            verification = self.validator.verify_patch(patch_content)
            
        self.assertTrue(verification.get("passed"))
        self.assertTrue(verification.get("static_passed"))
        self.assertTrue(verification.get("dynamic_passed"))

    def test_verify_patch_complete_pipeline_static_fail(self):
        patch_content = f"import os\nos.system('rm -rf /')"
        
        verification = self.validator.verify_patch(patch_content)
        
        self.assertFalse(verification.get("passed"))
        self.assertFalse(verification.get("static_passed"))
        self.assertFalse(verification.get("dynamic_passed", True))

    def test_patch_ast_inspection_detects_eval(self):
        code_with_eval = f"def {self.random_func}():\n    return eval('{random.randint(1, 50)}')"
        result = self.validator.analyze_static(code_with_eval)
        
        self.assertFalse(result.get("is_valid"))
        self.assertIn("eval", str(result.get("error")))

    def test_patch_ast_inspection_detects_exec(self):
        code_with_exec = f"def {self.random_func}():\n    exec('print({random.randint(51, 100)})')"
        result = self.validator.analyze_static(code_with_exec)
        
        self.assertFalse(result.get("is_valid"))
        self.assertIn("exec", str(result.get("error")))

    def test_stream_patch_validation_with_bytes_io(self):
        random_bytes = f"def {self.random_func}():\n    return '{uuid.uuid4().hex}'".encode('utf-8')
        stream = io.BytesIO(random_bytes)
        
        with patch('skills.patch_validator.sandbox_exec') as mock_sandbox:
            mock_sandbox.return_value = (True, "mocked_res", "")
            result = self.validator.verify_stream(stream)
            
        self.assertTrue(result.get("passed"))