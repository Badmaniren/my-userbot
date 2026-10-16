import unittest
import uuid
import random
import os
import tempfile
from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError, PatchSyntaxError
from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator

class TestPatchAutocorrectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.autocorrector = PatchAutocorrector(repo_path=self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_syntax_and_sanitization_flow(self):
        unique_var_name = f"var_{uuid.uuid4().hex[:8]}"
        unique_val = random.randint(100, 999)
        
        malformed_code = f"def compute_{unique_var_name}():\n    {unique_var_name} = {unique_val}\n    return {unique_var_name}\n"
        
        corrected_code = self.autocorrector.correct_syntax(malformed_code)
        self.assertIn(unique_var_name, corrected_code)

        sanitizer = CodeSanitizer(repo_path=self.repo_path)
        sanitized_code = sanitizer.sanitize_patch(corrected_code)
        
        validator = CodeValidator(repo_path=self.repo_path)
        is_valid = validator.validate_code(sanitized_code)
        self.assertTrue(is_valid)

    def test_integration_stream_processing_and_validation(self):
        stream_token = f"token_{uuid.uuid4().hex[:10]}"
        stream_content = f"x = '{stream_token}'\n"
        
        stream = tempfile.SpooledTemporaryFile(max_size=1024, mode='w+')
        stream.write(stream_content)
        stream.seek(0)
        
        transformed_code = self.autocorrector.transform_stream(stream)
        self.assertIn(stream_token, transformed_code)

        validated_result = self.autocorrector.correct_and_validate(transformed_code)
        self.assertEqual(validated_result, transformed_code)

    def test_integration_batch_correction(self):
        batch_id = uuid.uuid4().hex[:6]
        val1 = random.randint(1, 50)
        val2 = random.randint(51, 100)
        
        patch_dict = {
            f"patch_{batch_id}_1": f"a = {val1}\n",
            f"patch_{batch_id}_2": f"b = {val2}\n"
        }
        
        batch_results = self.autocorrector.batch_correct(patch_dict)
        self.assertEqual(len(batch_results), 2)
        for key, code in batch_results.items():
            self.assertIn(batch_id, key)
            self.assertTrue(len(code) > 0)

    def test_integration_syntax_error_raising(self):
        broken_syntax_code = f"def invalid_func_{uuid.uuid4().hex[:4]}():\n  print('unclosed string\n"
        
        with self.assertRaises(PatchSyntaxError):
            self.autocorrector.correct_syntax(broken_syntax_code)

if __name__ == '__main__':
    unittest.main()