import unittest
import uuid
import random
import os
import tempfile

from skills import patch_validator_engine
from skills.code_sanitizer import CodeSanitizerError
from skills.code_validator import CodeValidatorError
from skills.patch_sanitizer import PatchSanitizerError

class TestPatchValidatorEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.unique_id = str(uuid.uuid4())
        self.random_metric_value = random.uniform(1.0, 100.0)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_patch_validator_engine_pipeline_integration(self):
        malicious_code_snippet = f"print('Executing malicious payload {self.unique_id}')"

        with self.assertRaises((CodeSanitizerError, CodeValidatorError, PatchSanitizerError, Exception)):
            patch_validator_engine.validate_sanitized_patch(
                repo_path=self.repo_path,
                patch_data=malicious_code_snippet,
                threshold=self.random_metric_value
            )

        safe_patch_content = f"# Validated patch identifier: {self.unique_id}\nDATA_METRIC = {self.random_metric_value}\n"

        result = patch_validator_engine.validate_sanitized_patch(
            repo_path=self.repo_path,
            patch_data=safe_patch_content,
            threshold=self.random_metric_value
        )

        self.assertIsNotNone(result)
        if isinstance(result, dict):
            self.assertIn("status", result)
            self.assertEqual(result.get("identifier"), self.unique_id)
        else:
            self.assertTrue(hasattr(result, "status") or isinstance(result, bool))

if __name__ == "__main__":
    unittest.main()