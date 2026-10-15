import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.code_sanitizer import (
    CodeSanitizer,
    CodeSanitizerError,
    CodeAntipatternDetectedError
)


class TestCodeSanitizer(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.sanitizer = CodeSanitizer(repo_path=self.repo_path)

    def test_sanitize_valid_code_success(self):
        rand_var = f"var_{uuid.uuid4().hex[:8]}"
        rand_val = random.randint(100, 999)
        valid_code = f"def compute_{uuid.uuid4().hex[:6]}():\n    {rand_var} = {rand_val}\n    return {rand_var} * 2"
        
        cleaned_code = self.sanitizer.sanitize_patch(valid_code)
        
        self.assertIsInstance(cleaned_code, str)
        self.assertIn(rand_var, cleaned_code)
        self.assertIn(str(rand_val), cleaned_code)

    def test_detects_forbidden_except_pass_antipattern(self):
        rand_func = f"func_{uuid.uuid4().hex[:6]}"
        bad_code = f"def {rand_func}():\n    try:\n        x = 1 / 0\n    except Exception:\n        pass"
        
        with self.assertRaises(CodeAntipatternDetectedError) as ctx:
            self.sanitizer.sanitize_patch(bad_code)
        
        self.assertIn("except Exception", str(ctx.exception))

    def test_detects_forbidden_except_continue_antipattern(self):
        rand_loop_var = f"item_{uuid.uuid4().hex[:6]}"
        bad_code = f"for {rand_loop_var} in range(10):\n    try:\n        int({rand_loop_var})\n    except:\n        continue"
        
        with self.assertRaises(CodeAntipatternDetectedError) as ctx:
            self.sanitizer.sanitize_patch(bad_code)
            
        self.assertIn("continue", str(ctx.exception))

    def test_syntax_error_raises_sanitizer_error(self):
        rand_token = f"bad_{uuid.uuid4().hex[:6]}"
        invalid_syntax_code = f"def {rand_token}(\n    print('unclosed parenthesis'"
        
        with self.assertRaises(CodeSanitizerError) as ctx:
            self.sanitizer.sanitize_patch(invalid_syntax_code)
            
        self.assertIn("SyntaxError", str(ctx.exception))

    def test_stream_sanitization_with_io(self):
        rand_str = f"payload_{uuid.uuid4().hex}"
        stream_content = f"def process():\n    return '{rand_str}'".encode('utf-8')
        mock_stream = io.BytesIO(stream_content)
        
        result = self.sanitizer.sanitize_stream(mock_stream)
        
        self.assertIsInstance(result, str)
        self.assertIn(rand_str, result)

    def test_custom_antipattern_rule_injection(self):
        forbidden_word = f"eval_{uuid.uuid4().hex[:6]}"
        self.sanitizer.add_forbidden_pattern(forbidden_word)
        
        rand_arg = f"val_{uuid.uuid4().hex[:6]}"
        dangerous_code = f"def run_unsafe({rand_arg}):\n    return {forbidden_word}({rand_arg})"
        
        with self.assertRaises(CodeAntipatternDetectedError):
            self.sanitizer.sanitize_patch(dangerous_code)

    def test_batch_sanitization_mixed_results(self):
        rand_id_1 = uuid.uuid4().hex[:6]
        rand_id_2 = uuid.uuid4().hex[:6]
        
        patch_batch = {
            rand_id_1: f"def ok_{rand_id_1}(): return True",
            rand_id_2: f"def bad_{rand_id_2}():\n    try:\n        pass\n    except Exception:\n        pass"
        }
        
        results = self.sanitizer.batch_sanitize(patch_batch)
        
        self.assertIn(rand_id_1, results)
        self.assertTrue(results[rand_id_1]['is_valid'])
        
        self.assertIn(rand_id_2, results)
        self.assertFalse(results[rand_id_2]['is_valid'])
        self.assertIsNotNone(results[rand_id_2]['error'])