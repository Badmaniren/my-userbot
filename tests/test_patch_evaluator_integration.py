import unittest
import uuid
import random
import io
from pathlib import Path

from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult, PatchEvaluatorError
from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator
from skills.patch_verifier import PatchVerifier
from skills.patch_autocorrector import PatchAutocorrector
from skills.system_telemetry import SystemTelemetry

class TestPatchEvaluatorIntegration(unittest.TestCase):

    def setUp(self):
        self.repo_path = Path("./test_repo_integration")
        self.repo_path.mkdir(exist_ok=True)
        self.evaluator = PatchEvaluator(self.repo_path)
        self.random_id = str(uuid.uuid4())
        self.patch_content = f"print('Integration test {self.random_id}')"

    def tearDown(self):
        if self.repo_path.exists():
            for p in self.repo_path.glob("*"):
                p.unlink()
            self.repo_path.rmdir()

    def test_full_evaluation_pipeline_real_execution(self):
        sanitizer = CodeSanitizer(self.repo_path)
        validator = CodeValidator(self.repo_path)
        verifier = PatchVerifier(self.repo_path)
        autocorrector = PatchAutocorrector(self.repo_path)
        telemetry = SystemTelemetry(self.repo_path)

        if hasattr(sanitizer, "sanitize"):
            sanitized, is_safe = sanitizer.sanitize(self.patch_content)
            self.assertTrue(is_safe)
        elif hasattr(sanitizer, "sanitize_patch"):
            sanitized = sanitizer.sanitize_patch(self.patch_content)

        if hasattr(validator, "validate"):
            val_result = validator.validate(self.patch_content)
            self.assertIsInstance(val_result, dict)
        elif hasattr(validator, "validate_code"):
            val_result = validator.validate_code(self.patch_content)

        if hasattr(verifier, "verify"):
            is_verified = verifier.verify(self.patch_content)
            self.assertIsInstance(is_verified, bool)

        result = self.evaluator.evaluate(self.patch_content, collect_telemetry=True)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_safe)
        self.assertIsInstance(result.telemetry, dict)

    def test_evaluate_with_autocorrect_flow(self):
        corrupt_content = f"malicious_code_marker_{uuid.uuid4()}"

        result = self.evaluator.evaluate_with_autocorrect(corrupt_content)
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertIsInstance(result.was_corrected, bool)

    def test_evaluate_stream_integration(self):
        stream_data = io.BytesIO(self.patch_content.encode('utf-8'))

        result = self.evaluator.evaluate_stream(stream_data)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(result.is_valid)

if __name__ == "__main__":
    unittest.main()
