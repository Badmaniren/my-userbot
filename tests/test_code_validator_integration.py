import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.code_validator import CodeValidator, CodeValidatorError
from skills.code_sanitizer import CodeSanitizer, CodeAntipatternDetectedError


class TestCodeValidatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.validator = CodeValidator(repo_path=self.repo_path)
        self.sanitizer = CodeSanitizer(repo_path=self.repo_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_code_validator_with_sanitized_code_pipeline(self):
        unique_id = str(uuid.uuid4())
        metric_value = random.randint(100, 999)

        valid_raw_code = f"""
def compute_{unique_id.replace("-", "_")}():
    val = {metric_value}
    return val * 2
"""
        sanitized_code = self.sanitizer.sanitize_patch(valid_raw_code)
        
        is_valid = self.validator.validate_patch_ast(sanitized_code)
        self.assertTrue(is_valid, "Valid sanitized AST structure should pass validation.")

        forbidden_raw_code = f"""
def malicious_{unique_id.replace("-", "_")}():
    try:
        raise Exception("fail")
    except:
        pass
"""
        try:
            sanitized_forbidden = self.sanitizer.sanitize_patch(forbidden_raw_code)
        except CodeAntipatternDetectedError:
            sanitized_forbidden = None

        if sanitized_forbidden:
            with self.assertRaises((CodeValidatorError, CodeAntipatternDetectedError)):
                self.validator.validate_patch_ast(sanitized_forbidden)
        else:
            self.assertTrue(True, "Antipattern successfully caught before validation.")

    def test_batch_validation_flow(self):
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        codes = []
        for _ in range(3):
            uid = uuid.uuid4().hex[:6]
            val = random.random()
            code_snippet = f"x_{uid} = {val}\n"
            sanitized = self.sanitizer.sanitize_patch(code_snippet)
            codes.append(sanitized)

        batch_payload = {
            "batch_id": batch_id,
            "patches": codes
        }

        validation_results = self.validator.batch_validate(batch_payload)
        
        self.assertIsInstance(validation_results, dict)
        self.assertIn(batch_id, validation_results.get("batch_id", batch_id))
        self.assertTrue(len(validation_results.get("results", [])) == 3)
        for res in validation_results.get("results", []):
            self.assertTrue(res.get("is_valid", False))


if __name__ == "__main__":
    unittest.main()